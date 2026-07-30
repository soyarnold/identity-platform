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
uvicorn identity_api.main:app --reload --port 8000
```

## Lint / format / test

```bash
ruff check .
ruff format .
pytest
```

Auth endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `GET /me/sessions`, `POST /me/sessions/{id}/revoke`.

WebAuthn: `POST /webauthn/register/options|verify`, `POST /webauthn/login/options|verify`, `GET/PATCH/DELETE /me/passkeys`.

OAuth (AS): `GET /oauth/authorize`, `POST /oauth/consent`, `POST /oauth/token`, `GET /oauth/userinfo`, `GET /.well-known/oauth-authorization-server`. Dev helper: `POST /oauth/dev/clients`.

Admin (requires `is_admin`): `GET/PATCH /admin/users`, `GET /admin/audit-logs`, `GET/POST/PATCH/DELETE /admin/oauth/clients`.
