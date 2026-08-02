# Fieldkit — demo OAuth client

Public PKCE client that signs in via Identity Platform (Authorization Code + PKCE).

## Run

```bash
# API (:8000) + apps/web (:5173) should already be running
cd apps/demo
npm install
npm run dev
```

Open http://localhost:5174

## Register the client (once)

Prefer the monorepo seed (creates admin + this client):

```bash
./scripts/seed.sh
```

Or:

```bash
curl -sS -X POST http://localhost:8000/api/oauth/dev/clients \
  -H 'Content-Type: application/json' \
  -d '{"name":"Fieldkit Demo","client_id":"demo-app","redirect_uris":["http://localhost:5174/callback"],"is_confidential":false}'
```

Or create the same client in the admin panel (`/admin/clients`).

Third-party integrators (no repo): see [`docs/oauth-clients.md`](../../docs/oauth-clients.md).

## Flow

1. Click **Sign in with Identity Platform**
2. Browser → `GET /api/oauth/authorize` → hosted login/consent on `:5173`
3. Redirect to `/callback?code=&state=`
4. Demo exchanges code at `POST /api/oauth/token` and loads `GET /api/oauth/userinfo`

Local env: `VITE_API_URL`, `VITE_DEMO_CLIENT_ID`, `VITE_DEMO_REDIRECT_URI` (see root `.env.example`).
Shared-host Docker sets `VITE_BASE=/demo/` and empty `VITE_API_URL`.
