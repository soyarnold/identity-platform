# Deploy to Railway (portfolio / shared host)

One public HTTPS hostname serves:

| Path | App |
|------|-----|
| `/` | Identity web (dashboard + hosted OAuth login/consent) |
| `/demo/` | Fieldkit (OAuth client) |
| `/auth`, `/oauth`, `/me`, `/health`, … | FastAPI (nginx → uvicorn unix socket) |

Postgres + Redis are Railway plugins. No custom domain required for cookies: everything is same-origin, so the HttpOnly `sid` cookie works.

```text
Browser → https://HOST  (Railway public domain → TCP $PORT, usually 8080)
            │
            ▼
          nginx (only public TCP listener)
            ├─ /          Identity web (static)
            ├─ /demo/     Fieldkit (static)
            └─ /oauth/…   proxy → unix:/tmp/uvicorn.sock (FastAPI)
```

**Do not confuse local ports with Railway:**

| Port | Local dev | Railway container |
|------|-----------|-------------------|
| `8000` | uvicorn directly | **Not used** (API is a unix socket) |
| `5173` / `5174` | Vite web / demo | N/A (built into static files) |
| `8080` (`$PORT`) | optional local Docker | **nginx — set the domain target port to this** |

## 1. Create the project

1. In [Railway](https://railway.app), **New Project**.
2. Add **PostgreSQL** and **Redis** plugins (same project).
3. Add a **service** from this GitHub repo (or deploy from CLI).
4. **Builder must be Dockerfile** — this monorepo is not Railpack-friendly.
   - Repo includes [`railway.json`](../railway.json) with `"builder": "DOCKERFILE"`.
   - Or in the service **Settings → Build**: set builder to **Dockerfile**, path `Dockerfile`.
   - Root directory = monorepo root (where `Dockerfile` lives).
5. Generate a public URL — call it `https://HOST` (e.g. `https://identity-platform-production.up.railway.app`).
6. **Networking (required):** on that domain, set **Port / target port to `8080`** (or whatever `$PORT` Railway injects — must match nginx).  
   - **Never use `8000`** for the public domain. That is the local uvicorn port only.  
   - Symptom if wrong: deploy logs show `/health` 200, but the browser gets edge **502** for `/`, `/demo/`, and `/health`.

If the build log says **Railpack** and `railpack process exited with an error`, Railway ignored the Dockerfile. Fix the builder setting above and redeploy.

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
| `PORT` | Set by Railway (nginx listens here; domain target port must match) |

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
3. uvicorn on `unix:/tmp/uvicorn.sock` + nginx on `$PORT`

Health check path: `/health` (must go through nginx on `$PORT`).

Healthy deploy log markers:

```text
Starting uvicorn on unix:/tmp/uvicorn.sock...
Starting nginx on 0.0.0.0:8080 (only public TCP port)...
… "GET /health HTTP/1.1" 200 OK
```

## 4. Smoke test (GIF path)

1. `https://HOST/health` → 200 (not Railway JSON 502).
2. Open `https://HOST/demo/` → **Sign in with Identity Platform**.
3. Register or sign in on hosted UI (`/oauth/login` …).
4. **Allow** on consent.
5. Land on `https://HOST/demo/callback` → Fieldkit shows email / `sub`.
6. Optional: `https://HOST/` with seed admin → dashboard / `/admin`.

If consent loops or “not authenticated”: confirm `FRONTEND_URL`, `COOKIE_SECURE=true`, and that you are not mixing `http`/`https` or a second hostname.

If authorize fails with invalid redirect: update seed `DEMO_REDIRECT_URI` (or admin Clients) to exactly `https://HOST/demo/callback`, redeploy or re-run seed.

## 5. Troubleshooting (502 / “Application failed to respond”)

| What you see | Likely cause | Fix |
|--------------|--------------|-----|
| Public 502; domain **Port 8000** | Edge aimed at old local uvicorn port | Set domain port to **8080** |
| Deploy log health 200, browser 502 | Same port mismatch | Networking → port **8080** |
| Container exits after “Starting nginx” | Old entrypoint killed uvicorn on `exec` | Use current `deploy/entrypoint.sh` (no `exec` + EXIT trap) |
| Railpack build failure | Wrong builder | Force **Dockerfile** via `railway.json` / settings |
| No DB / Redis | Plugins not linked | Add Postgres + Redis; reference `DATABASE_URL` / `REDIS_URL` |
| OAuth redirect rejected | Seed still has localhost callback only | Set `DEMO_REDIRECT_URI=https://HOST/demo/callback`, redeploy |

**502 during `image push` is normal** — wait until **Healthcheck succeeded** before testing the URL.

## 6. Local Docker (optional)

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
