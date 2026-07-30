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
uvicorn identity_api.main:app --reload --port 8000
```

API health: http://localhost:8000/health

### Auth (phase 02)

```bash
cd apps/api && source .venv/bin/activate
alembic upgrade head
uvicorn identity_api.main:app --reload --port 8000
```

- `POST /auth/register` / `POST /auth/login` / `POST /auth/logout` / `GET /auth/me`
- `GET /me/sessions` / `POST /me/sessions/{id}/revoke`
- WebAuthn (phase 03): `POST /webauthn/register|login/options|verify`, `GET/PATCH/DELETE /me/passkeys`
- CI: `.github/workflows/ci.yml` (ruff + pytest with Postgres/Redis services)

## Tooling

- **Ruff** — lint and format (`apps/api`)
- **pytest** — API tests under `apps/api/tests`
