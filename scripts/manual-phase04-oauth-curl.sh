#!/usr/bin/env bash
# Manual OAuth PKCE smoke checks for phase 04.
# Prerequisites: API running on :8000, migrations through 0003_oauth.
#
#   ./scripts/manual-phase04-oauth-curl.sh

set -euo pipefail

API="${API:-http://localhost:8000}"
JAR="${JAR:-/tmp/identity-phase04.jar}"
EMAIL="${EMAIL:-oauth-manual@example.com}"
PASSWORD="${PASSWORD:-password123}"
CLIENT_ID="${CLIENT_ID:-demo-app}"
REDIRECT_URI="${REDIRECT_URI:-http://localhost:5174/callback}"

rm -f "$JAR"

echo "== register / login =="
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq . || true
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq .

echo
echo "== create public OAuth client (dev helper) =="
curl -sS -X POST "$API/oauth/dev/clients" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Demo App\",\"client_id\":\"$CLIENT_ID\",\"redirect_uris\":[\"$REDIRECT_URI\"],\"is_confidential\":false}" | jq .

# PKCE S256 via python
read -r VERIFIER CHALLENGE < <(python3 - <<'PY'
import base64, hashlib, secrets
v = secrets.token_urlsafe(64)
c = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).decode().rstrip("=")
print(v, c)
PY
)

STATE="manual-state"
echo
echo "== authorize (logged in → consent redirect) =="
curl -sS -c "$JAR" -b "$JAR" -D - -o /dev/null \
  "$API/oauth/authorize?client_id=$CLIENT_ID&redirect_uri=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$REDIRECT_URI'''))")&response_type=code&code_challenge=$CHALLENGE&code_challenge_method=S256&state=$STATE&scope=openid%20profile%20email" \
  | tr -d '\r' | grep -i '^location:' || true

echo
echo "== consent =="
CONSENT="$(curl -sS -c "$JAR" -b "$JAR" -X POST "$API/oauth/consent" \
  -H 'Content-Type: application/json' \
  -d "{\"client_id\":\"$CLIENT_ID\",\"redirect_uri\":\"$REDIRECT_URI\",\"response_type\":\"code\",\"code_challenge\":\"$CHALLENGE\",\"code_challenge_method\":\"S256\",\"state\":\"$STATE\",\"scope\":\"openid profile email\",\"approve\":true}")"
echo "$CONSENT" | jq .
REDIRECT_TO="$(echo "$CONSENT" | jq -r .redirect_to)"
CODE="$(python3 - <<PY
from urllib.parse import urlparse, parse_qs
print(parse_qs(urlparse("$REDIRECT_TO").query)["code"][0])
PY
)"

echo
echo "== token =="
TOKEN="$(curl -sS -X POST "$API/oauth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=authorization_code&code=$CODE&redirect_uri=$REDIRECT_URI&client_id=$CLIENT_ID&code_verifier=$VERIFIER")"
echo "$TOKEN" | jq .
ACCESS="$(echo "$TOKEN" | jq -r .access_token)"

echo
echo "== userinfo =="
curl -sS "$API/oauth/userinfo" -H "Authorization: Bearer $ACCESS" | jq .

echo
echo "== discovery =="
curl -sS "$API/.well-known/oauth-authorization-server" | jq .

echo
echo "Done."
