# Identity Platform API

FastAPI authorization server for the Identity Platform monorepo.

## Setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
# from repo root
docker compose up -d
cd apps/api
alembic upgrade head
python -m identity_api.seed
uvicorn identity_api.main:app --reload --port 8000
```

Seed creates the admin user and `demo-app` OAuth client (idempotent; see `.env` `SEED_*` / `DEMO_*`).

## Lint / format / test

```bash
ruff check .
ruff format .
pytest
```

Auth endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/me/sessions`, `POST /api/me/sessions/{id}/revoke`.

WebAuthn: `POST /api/webauthn/register/options|verify`, `POST /api/webauthn/login/options|verify`, `GET/PATCH/DELETE /api/me/passkeys`.

OAuth (AS): `GET /api/oauth/authorize`, `POST /api/oauth/consent`, `POST /api/oauth/token`, `GET /api/oauth/userinfo`, `GET /api/.well-known/oauth-authorization-server`. Dev helper: `POST /api/oauth/dev/clients` (requires `ENABLE_DEV_OAUTH_CLIENTS=true`).

Admin (requires `is_admin`): `GET/PATCH /api/admin/users`, `GET /api/admin/audit-logs`, `GET/POST/PATCH/DELETE /api/admin/oauth/clients`.

Third-party OAuth client integration (no repo required): see `/docs/oauth-clients.md` at the monorepo root.
