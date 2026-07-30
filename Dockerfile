# syntax=docker/dockerfile:1
# Single Railway host: Identity web (/) + Fieldkit (/demo/) + FastAPI (same origin).
# Build from monorepo root: docker build -t identity-platform .

# ---------------------------------------------------------------------------
# Identity web (apps/web)
# ---------------------------------------------------------------------------
FROM node:22-bookworm-slim AS web-build
WORKDIR /src
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
# Empty VITE_API_URL → same-origin relative fetches (wired in a later todo if needed)
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ---------------------------------------------------------------------------
# Fieldkit (apps/demo) under /demo/
# ---------------------------------------------------------------------------
FROM node:22-bookworm-slim AS demo-build
WORKDIR /src
COPY apps/demo/package.json apps/demo/package-lock.json ./
RUN npm ci
COPY apps/demo/ ./
ARG VITE_API_URL=
ARG VITE_DEMO_REDIRECT_URI=
ARG VITE_DEMO_CLIENT_ID=demo-app
ENV VITE_API_URL=$VITE_API_URL \
    VITE_DEMO_REDIRECT_URI=$VITE_DEMO_REDIRECT_URI \
    VITE_DEMO_CLIENT_ID=$VITE_DEMO_CLIENT_ID
# Asset base /demo/; React Router basename lands in the next todo
RUN npm run build -- --base=/demo/

# ---------------------------------------------------------------------------
# Python API deps
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS api-build
WORKDIR /src
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/src ./src
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./
RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Runtime: nginx + uvicorn
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

WORKDIR /app/api
COPY --from=api-build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=api-build /usr/local/bin /usr/local/bin
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./
COPY apps/api/src ./src
ENV PYTHONPATH=/app/api/src

COPY --from=web-build /src/dist /usr/share/nginx/html
COPY --from=demo-build /src/dist /usr/share/nginx/html/demo

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PORT=8080
EXPOSE 8080
CMD ["/entrypoint.sh"]
