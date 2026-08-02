# Local vs Railway env (cheat sheet). Full steps: docs/deploy-railway.md

# --- Local (Compose + Vite on :5173 / :5174) ---
# VITE_API_URL=http://localhost:8000
# FRONTEND_URL=http://localhost:5173
# DEMO_REDIRECT_URI=http://localhost:5174/callback
# WEBAUTHN_RP_ID=localhost
# COOKIE_SECURE=false
# ENABLE_DEV_OAUTH_CLIENTS=true

# --- Railway (one HOST; Dockerfile sets VITE_BASE=/demo/ + empty VITE_API_URL) ---
# Networking: domain port = 8080 ($PORT). Never 8000.
# Do not set any VITE_* on the service.
#   DATABASE_URL / REDIS_URL   (plugins)
#   SECRET_KEY
#   FRONTEND_URL=https://HOST
#   CORS_ORIGINS=https://HOST
#   DEMO_REDIRECT_URI=https://HOST/demo/callback
#   WEBAUTHN_RP_ID=HOST          # hostname only
#   WEBAUTHN_ORIGINS=https://HOST
#   COOKIE_SECURE=true
#   ENABLE_DEV_OAUTH_CLIENTS=false
