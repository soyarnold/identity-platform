#!/bin/sh
# Railway / container entrypoint: migrate → seed → API + nginx on $PORT.
set -eu

PORT="${PORT:-8080}"
API_HOST="127.0.0.1"
API_PORT="8000"

# nginx listen port (Railway injects PORT)
sed -i "s/listen 8080;/listen ${PORT};/" /etc/nginx/conf.d/default.conf

cd /app/api

echo "Running migrations..."
alembic upgrade head

echo "Seeding admin + demo OAuth client..."
python -m identity_api.seed

echo "Starting uvicorn on ${API_HOST}:${API_PORT}..."
uvicorn identity_api.main:app \
  --host "${API_HOST}" \
  --port "${API_PORT}" \
  --proxy-headers \
  --forwarded-allow-ips='*' &
UVICORN_PID=$!

# Wait until API accepts connections before opening nginx
i=0
while [ "$i" -lt 60 ]; do
  if python -c "import urllib.request; urllib.request.urlopen('http://${API_HOST}:${API_PORT}/health', timeout=1)" 2>/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.5
done

echo "Starting nginx on port ${PORT}..."
nginx -g 'daemon off;' &
NGINX_PID=$!

shutdown() {
  echo "Shutting down..."
  kill -TERM "${NGINX_PID}" 2>/dev/null || true
  kill -TERM "${UVICORN_PID}" 2>/dev/null || true
  wait "${NGINX_PID}" 2>/dev/null || true
  wait "${UVICORN_PID}" 2>/dev/null || true
}
trap 'shutdown; exit 0' TERM INT

# Stay up while both children are alive (POSIX: no wait -n).
while kill -0 "${UVICORN_PID}" 2>/dev/null && kill -0 "${NGINX_PID}" 2>/dev/null; do
  sleep 1
done

echo "A supervised process exited."
shutdown
exit 1
