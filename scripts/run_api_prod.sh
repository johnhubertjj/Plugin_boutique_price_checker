#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export APP_ENV=production
export DB_AUTO_CREATE=false
export AUTH_DEV_MODE=false
uv run python -m uvicorn plugin_boutique_price_checker.web.api:app --host 0.0.0.0 --port "${PORT:-8080}"

