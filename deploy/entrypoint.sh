#!/bin/sh
# Railway / container entrypoint: migrate → seed → API (unix socket) + nginx on $PORT.
set -eu

PORT="${PORT:-8080}"
UVICORN_SOCK="/tmp/uvicorn.sock"

# nginx listen port (Railway injects PORT). Match both IPv4 and IPv6 listen lines.
sed -i "s/listen 8080;/listen ${PORT};/g" /etc/nginx/conf.d/default.conf
sed -i "s/listen \[::\]:8080;/listen [::]:${PORT};/g" /etc/nginx/conf.d/default.conf

cd /app/api

echo "Running migrations..."
alembic upgrade head

echo "Seeding admin + demo OAuth client..."
python -m identity_api.seed

rm -f "${UVICORN_SOCK}"
echo "Starting uvicorn on unix:${UVICORN_SOCK}..."
uvicorn identity_api.main:app \
  --uds "${UVICORN_SOCK}" \
  --proxy-headers \
  --forwarded-allow-ips='*' &
UVICORN_PID=$!

# Wait until the socket exists and accepts connections
i=0
while [ "$i" -lt 60 ]; do
  if [ -S "${UVICORN_SOCK}" ] && \
     python -c "import socket; s=socket.socket(socket.AF_UNIX); s.settimeout(1); s.connect('${UVICORN_SOCK}'); s.close()" 2>/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.5
done

if [ ! -S "${UVICORN_SOCK}" ]; then
  echo "uvicorn socket did not become ready" >&2
  exit 1
fi

# nginx worker must be able to read/write the socket (uvicorn creates it as the
# current user; make it world-accessible within the container).
chmod 666 "${UVICORN_SOCK}" 2>/dev/null || true

echo "Starting nginx on 0.0.0.0:${PORT} (only public TCP port)..."
nginx -g 'daemon off;' &
NGINX_PID=$!

shutdown() {
  echo "Shutting down..."
  kill -TERM "${NGINX_PID}" 2>/dev/null || true
  kill -TERM "${UVICORN_PID}" 2>/dev/null || true
  wait "${NGINX_PID}" 2>/dev/null || true
  wait "${UVICORN_PID}" 2>/dev/null || true
  rm -f "${UVICORN_SOCK}"
}
trap 'shutdown; exit 0' TERM INT

# Stay up while both children are alive (POSIX: no wait -n).
while kill -0 "${UVICORN_PID}" 2>/dev/null && kill -0 "${NGINX_PID}" 2>/dev/null; do
  sleep 1
done

echo "A supervised process exited."
shutdown
exit 1
