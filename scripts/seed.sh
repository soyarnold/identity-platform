#!/usr/bin/env bash
# Idempotent seed: admin user + demo OAuth client (Fieldkit).
# Prerequisites: Compose up, migrations applied.
#
#   ./scripts/seed.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"

if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python -m identity_api.seed
