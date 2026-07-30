# Env notes for local vs shared-host Railway deploy.
# Full click-ops: docs/deploy-railway.md (later todo).

# --- Local (Compose + host processes) ---
# VITE_API_URL=http://localhost:8000
# FRONTEND_URL=http://localhost:5173
# DEMO_REDIRECT_URI=http://localhost:5174/callback
# WEBAUTHN_RP_ID=localhost
# WEBAUTHN_ORIGINS=http://localhost:5173,http://localhost:5174
# COOKIE_SECURE=false
# COOKIE_DOMAIN=

# --- Railway single HOST (e.g. https://xxx.up.railway.app) ---
# Build args: VITE_API_URL=  (empty = same-origin)  VITE_BASE=/demo/ (Dockerfile)
# Runtime:
#   FRONTEND_URL=https://HOST
#   CORS_ORIGINS=https://HOST
#   DEMO_REDIRECT_URI=https://HOST/demo/callback
#   WEBAUTHN_RP_ID=HOST          # hostname only, no https://
#   WEBAUTHN_ORIGINS=https://HOST
#   COOKIE_SECURE=true
#   COOKIE_DOMAIN=               # leave empty (host-only sid cookie)
#   ENABLE_DEV_OAUTH_CLIENTS=false
#   SECRET_KEY=<strong random>
#   DATABASE_URL from Railway Postgres plugin is fine as postgres://
#     (normalized to postgresql+asyncpg:// in Settings)
