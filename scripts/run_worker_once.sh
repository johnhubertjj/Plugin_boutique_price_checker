#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export APP_ENV=production
export DB_AUTO_CREATE=false
export WORKER_RUN_ONCE=true
uv run plugin-boutique-worker

