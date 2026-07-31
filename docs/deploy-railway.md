# Deploy to Railway (portfolio / shared host)

One public HTTPS hostname serves:

| Path | App |
|------|-----|
| `/` | Identity web (dashboard + hosted OAuth login/consent) |
| `/demo/` | Fieldkit (OAuth client) |
| `/auth`, `/oauth`, `/me`, … | FastAPI (proxied by nginx → uvicorn) |

Postgres + Redis are Railway plugins. No custom domain required for cookies: everything is same-origin, so the HttpOnly `sid` cookie works.

```text
Browser → https://HOST
            ├─ /          Identity web (static)
            ├─ /demo/     Fieldkit (static)
            └─ /oauth/…   API (uvicorn)
```

## 1. Create the project

1. In [Railway](https://railway.app), **New Project**.
2. Add **PostgreSQL** and **Redis** plugins (same project).
3. Add a **service** from this GitHub repo (or deploy from CLI).
4. **Builder must be Dockerfile** — this monorepo is not Railpack-friendly.
   - Repo includes [`railway.json`](../railway.json) with `"builder": "DOCKERFILE"`.
   - Or in the service **Settings → Build**: set builder to **Dockerfile**, path `Dockerfile`.
   - Root directory = monorepo root (where `Dockerfile` lives).
5. Generate / copy the public URL — call it `https://HOST` (e.g. `https://identity-platform-production.up.railway.app`).
6. **Networking → public port / target port must be `$PORT` (usually `8080`)**, where nginx listens. Do **not** point traffic at `8000` — the API is only on a Unix socket inside the container.

If the build log says **Railpack** and `railpack process exited with an error`, Railway ignored the Dockerfile. Fix the builder setting above and redeploy.

If deploy logs show `/health` 200 but the public URL is 502, the domain is almost always aimed at the wrong port — set the service target port to `8080` (or whatever `$PORT` is) and redeploy.

## 2. Runtime environment variables

Set these on the **web/API service** (not only in a local `.env`). Replace `HOST` with the hostname only where noted.

| Variable | Example / notes |
|----------|-----------------|
| `DATABASE_URL` | From Postgres plugin (reference variable). `postgres://` is OK — rewritten to `postgresql+asyncpg://`. |
| `REDIS_URL` | From Redis plugin. |
| `SECRET_KEY` | Long random string (not the local default). |
| `FRONTEND_URL` | `https://HOST` |
| `CORS_ORIGINS` | `https://HOST` |
| `DEMO_REDIRECT_URI` | `https://HOST/demo/callback` |
| `DEMO_CLIENT_ID` | `demo-app` (default) |
| `DEMO_CLIENT_NAME` | `Fieldkit Demo` (optional) |
| `SEED_ADMIN_EMAIL` | e.g. `admin@example.com` |
| `SEED_ADMIN_PASSWORD` | Strong password for the seeded admin |
| `WEBAUTHN_RP_ID` | **Hostname only**, e.g. `identity-platform-production.up.railway.app` |
| `WEBAUTHN_ORIGINS` | `https://HOST` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_DOMAIN` | Leave empty |
| `ENABLE_DEV_OAUTH_CLIENTS` | `false` |
| `PORT` | Usually set by Railway |

Also set seed/demo vars if you override defaults so boot seed matches Fieldkit’s redirect URI.

### Build-time (Dockerfile)

The image already builds with:

- `VITE_API_URL=` (empty → same-origin `/auth`, `/oauth/...`)
- Fieldkit `VITE_BASE=/demo/`

If you need a fixed redirect baked into the JS bundle, pass build arg:

`VITE_DEMO_REDIRECT_URI=https://HOST/demo/callback`

Otherwise Fieldkit derives redirect from `window.location` + `/demo/callback` at runtime. **Seed/DB** must still list that exact URI on the `demo-app` client.

## 3. Deploy

Push the branch Railway watches (or **Deploy** from the dashboard). On each start, [`deploy/entrypoint.sh`](../deploy/entrypoint.sh):

1. `alembic upgrade head`
2. `python -m identity_api.seed` (admin + `demo-app`)
3. uvicorn + nginx on `$PORT`

Health check path: `/health`.

## 4. Smoke test (GIF path)

1. Open `https://HOST/demo/` → **Sign in with Identity Platform**.
2. Register or sign in on hosted UI (`/oauth/login` …).
3. **Allow** on consent.
4. Land on `https://HOST/demo/callback` → Fieldkit shows email / `sub`.
5. Optional: `https://HOST/` with seed admin → dashboard / `/admin`.

If consent loops or “not authenticated”: confirm `FRONTEND_URL`, `COOKIE_SECURE=true`, and that you are not mixing `http`/`https` or a second hostname.

If authorize fails with invalid redirect: update seed `DEMO_REDIRECT_URI` (or admin Clients) to exactly `https://HOST/demo/callback`, redeploy or re-run seed.

## 5. Local Docker (optional)

From monorepo root (Postgres/Redis already via Compose):

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

Then open `http://localhost:8080/demo/`.

## Related

- Env cheat sheet: [`deploy/ENV.md`](../deploy/ENV.md)
- Third-party OAuth (no repo): [`docs/oauth-clients.md`](oauth-clients.md)
- CDK scaffold (not this deploy): [`infra/README.md`](../infra/README.md)
