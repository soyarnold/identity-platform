# Identity Platform

Passwordless-capable identity provider (email/password + WebAuthn) with sessions, an OAuth 2.0 + PKCE authorization server, auth dashboard, admin panel, and a demo third-party app.

## Stack

- **API**: FastAPI, PostgreSQL, Redis (`apps/api`)
- **Web**: Vite + React — dashboard, admin, hosted OAuth UI (`apps/web`)
- **Demo**: Vite + React OAuth client (`apps/demo`)
- **Infra**: AWS CDK scaffold (`infra`) — local Docker Compose for Postgres/Redis

## Quick start (local)

```bash
cp .env.example .env
docker compose up -d

cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn identity_api.main:app --reload --port 8000
```

API health: http://localhost:8000/health

### Auth dashboard (phase 05)

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:5173 — register/login, passkeys, sessions (API on `:8000`).

## API surface (summary)

- Auth: `POST /auth/register|login|logout`, `GET /auth/me`
- Sessions: `GET /me/sessions`, `POST /me/sessions/{id}/revoke`
- WebAuthn: `POST /webauthn/register|login/options|verify`, `GET/PATCH/DELETE /me/passkeys`
- OAuth AS: authorize/consent/token/userinfo + PKCE; `POST /oauth/dev/clients` for local testing
- CI: `.github/workflows/ci.yml` (ruff + pytest)

## Tooling

- **Ruff** — lint and format (`apps/api`)
- **pytest** — API tests under `apps/api/tests`
