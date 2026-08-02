# Deploy to Railway (portfolio / shared host)

One HTTPS host:

| Path | Serves |
|------|--------|
| `/` | Identity web |
| `/demo/` | Fieldkit |
| `/auth`, `/oauth`, `/me`, `/health`, … | API (nginx → uvicorn) |

```text
Browser → HOST:$PORT (usually 8080)
            └─ nginx
                 ├─ /demo/*  → static Fieldkit
                 ├─ /oauth/* → unix socket → FastAPI
                 └─ /*       → static Identity web
```

**Local vs Railway ports:** `8000` is only local uvicorn. Railway public domain port must be **`8080`** (`$PORT` / nginx).

## Setup

1. New Railway project + **PostgreSQL** + **Redis**.
2. Service from this repo; builder **Dockerfile** (see `railway.json`). Root = monorepo root.
3. Public domain → **port 8080** (not 8000).
4. Set runtime env (see [`deploy/ENV.md`](../deploy/ENV.md)). No `VITE_*` variables.
5. Deploy. Boot runs migrate → seed → uvicorn (socket) + nginx.

Healthy logs include: `Uvicorn running on unix socket` and `Starting nginx on 0.0.0.0:8080`.

## Smoke test

1. `https://HOST/health` → 200  
2. `https://HOST/demo/` → Sign in → consent → `/demo/callback`  
3. Optional: `https://HOST/` with seed admin  

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Public 502, logs healthy | Domain port → **8080** |
| Sign-in goes to `localhost:8000` | Remove `VITE_*` from Railway; redeploy |
| Invalid OAuth redirect | `DEMO_REDIRECT_URI=https://HOST/demo/callback`, redeploy |
| Railpack build error | Force Dockerfile builder |

## Local Docker (optional)

```bash
docker compose up -d
docker build -t identity-platform .
docker run --rm -p 8080:8080 \
  -e DATABASE_URL=postgresql+asyncpg://identity:identity@host.docker.internal:5432/identity \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e SECRET_KEY=local-docker-secret \
  -e FRONTEND_URL=http://localhost:8080 \
  -e CORS_ORIGINS=http://localhost:8080 \
  -e DEMO_REDIRECT_URI=http://localhost:8080/demo/callback \
  -e WEBAUTHN_RP_ID=localhost \
  -e WEBAUTHN_ORIGINS=http://localhost:8080 \
  -e COOKIE_SECURE=false \
  -e ENABLE_DEV_OAUTH_CLIENTS=false \
  identity-platform
```

## Related

- [`deploy/ENV.md`](../deploy/ENV.md) · [`docs/oauth-clients.md`](oauth-clients.md) · [`infra/README.md`](../infra/README.md)
