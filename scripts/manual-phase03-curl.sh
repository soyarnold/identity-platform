#!/usr/bin/env bash
# Manual smoke checks for phase 03 (auth + sessions + WebAuthn options).
# Prerequisites:
#   docker compose up -d
#   cd apps/api && alembic upgrade head && uvicorn identity_api.main:app --reload --port 8000
#
# Usage:
#   chmod +x scripts/manual-phase03-curl.sh
#   ./scripts/manual-phase03-curl.sh           # run all password/session checks
#   ./scripts/manual-phase03-curl.sh options   # also hit WebAuthn register options
#
# Cookie jar: /tmp/identity-phase03.jar

set -euo pipefail

API="${API:-http://localhost:8000}"
JAR="${JAR:-/tmp/identity-phase03.jar}"
EMAIL="${EMAIL:-manual@example.com}"
PASSWORD="${PASSWORD:-password123}"

rm -f "$JAR"

echo "== health =="
curl -sS "$API/health" | jq .

echo
echo "== register ($EMAIL) =="
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq .

echo
echo "== me =="
curl -sS -c "$JAR" -b "$JAR" "$API/auth/me" | jq .

echo
echo "== sessions =="
SESSIONS="$(curl -sS -c "$JAR" -b "$JAR" "$API/me/sessions")"
echo "$SESSIONS" | jq .
SESSION_ID="$(echo "$SESSIONS" | jq -r '.[0].id // empty')"

echo
echo "== passkeys (should be empty before registering a real passkey) =="
curl -sS -c "$JAR" -b "$JAR" "$API/me/passkeys" | jq .

echo
echo "== webauthn register options (challenge only; no real passkey created) =="
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/webauthn/register/options" | jq .

if [[ "${1:-}" == "options" || "${1:-}" == "all" ]]; then
  echo
  echo "== webauthn login options (fails until a passkey exists) =="
  curl -sS -X POST "$API/webauthn/login/options" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\"}" | jq . || true
fi

echo
echo "== logout =="
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/auth/logout" | jq .

echo
echo "== me after logout (expect 401) =="
curl -sS -c "$JAR" -b "$JAR" -w "\nHTTP %{http_code}\n" "$API/auth/me" || true

echo
echo "== login =="
curl -sS -c "$JAR" -b "$JAR" -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" | jq .

echo
echo "== me after login =="
curl -sS -c "$JAR" -b "$JAR" "$API/auth/me" | jq .

if [[ -n "$SESSION_ID" ]]; then
  echo
  echo "== revoke a prior session id if still present ($SESSION_ID) =="
  curl -sS -c "$JAR" -b "$JAR" -X POST "$API/me/sessions/$SESSION_ID/revoke" | jq . || true
fi

echo
echo "Done. Cookie jar: $JAR"
echo "Note: full passkey create/login needs a browser (phase 05 dashboard)."
