# Identity Platform

Clerk/Auth0-style identity provider: email/password + WebAuthn, sessions, OAuth 2.0 + PKCE authorization server, auth dashboard, admin panel, and a demo third-party client.

## Stack

| Piece | Location |
|-------|----------|
| API (FastAPI) | `apps/api` |
| Dashboard + hosted OAuth UI | `apps/web` (`:5173`) |
| Demo OAuth client (Fieldkit) | `apps/demo` (`:5174`) |
| Postgres + Redis (local) | `docker-compose.yml` |
| AWS CDK scaffold | `infra/` (not deployable yet) |

**Ports:** API `8000`, web `5173`, demo `5174`, Postgres `5432`, Redis `6379`.

## Quick start (local)

```bash
cp .env.example .env
docker compose up -d

cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
python -m identity_api.seed    # admin + demo-app client
uvicorn identity_api.main:app --reload --port 8000
```

In other terminals:

```bash
cd apps/web && npm install && npm run dev     # http://localhost:5173
cd apps/demo && npm install && npm run dev    # http://localhost:5174
```

**Seed defaults** (from `.env`):

| | |
|--|--|
| Admin | `admin@example.com` / `AdminPassword123!` |
| OAuth client | `demo-app` → `http://localhost:5174/callback` |

Sign in at the dashboard with the admin user, or open Fieldkit and use **Sign in with Identity Platform**.

Re-run seed anytime (idempotent): `./scripts/seed.sh`

## Docs by audience

| Audience | Start here |
|----------|------------|
| Running this monorepo | This README (quick start above) |
| **Deploy to Railway** (portfolio / shared host) | [`docs/deploy-railway.md`](docs/deploy-railway.md) |
| **Third-party app** integrating as an OAuth client (no repo access) | [`docs/oauth-clients.md`](docs/oauth-clients.md) |
| API details | [`apps/api/README.md`](apps/api/README.md) |
| Demo client | [`apps/demo/README.md`](apps/demo/README.md) |
| Future AWS layout | [`infra/README.md`](infra/README.md) |

### Product surfaces (after seed)

- **Dashboard** (`:5173`) — register/login, passkeys, sessions; admin nav if `is_admin`
- **Hosted OAuth** — `/oauth/login`, `/oauth/register`, `/oauth/consent` (linked from `GET /oauth/authorize`)
- **Admin** — `/admin/users`, `/admin/audit`, `/admin/clients`
- **Fieldkit** (`:5174`) — public PKCE client against this AS

## API surface (summary)

- Auth: `POST /auth/register|login|logout`, `GET /auth/me`
- Sessions: `GET /me/sessions`, `POST /me/sessions/{id}/revoke`
- WebAuthn: `POST /webauthn/register|login/options|verify`, passkey CRUD under `/me/passkeys`
- OAuth AS: authorize / consent / token / userinfo + PKCE; discovery at `/.well-known/oauth-authorization-server`
- Admin: `/admin/users`, `/admin/audit-logs`, `/admin/oauth/clients` (requires `is_admin`)
- Dev helper: `POST /oauth/dev/clients` (local only when `ENABLE_DEV_OAUTH_CLIENTS=true`; prefer admin or seed)

## CI / PRs

- GitHub Actions (`.github/workflows/ci.yml`): Ruff + pytest with Postgres/Redis services
- Feature work: one branch at a time from `main`; open a PR to merge (no auto-deploy)
- CDK is scaffold-only — no deploy workflow yet

## Tooling

- **Ruff** + **pytest** — `apps/api`
- Manual OAuth curls — `scripts/manual-phase04-oauth-curl.sh`
- Seed — `scripts/seed.sh` / `python -m identity_api.seed`
