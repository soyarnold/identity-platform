#!/usr/bin/env bash
# Railway / container entrypoint: migrate → seed → API + nginx on $PORT.
set -euo pipefail

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

cleanup() {
  kill "${UVICORN_PID}" 2>/dev/null || true
}
trap cleanup EXIT

# Wait until API accepts connections before opening nginx
for _ in $(seq 1 60); do
  if python -c "import urllib.request; urllib.request.urlopen('http://${API_HOST}:${API_PORT}/health', timeout=1)" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

echo "Starting nginx on port ${PORT}..."
exec nginx -g 'daemon off;'
