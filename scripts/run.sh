#!/usr/bin/env bash
# Convenience wrapper: ./scripts/run.sh [smoke|ui|api|live|no-live]
set -euo pipefail
cd "$(dirname "$0")/.."

case "${1:-smoke}" in
  smoke)   cd ui && npx playwright test tests/smoke ;;
  ui)      cd ui && npx playwright test ;;
  api)     cd api && uv run pytest -v ;;
  live)    cd ui && npx playwright test --grep @live ;;
  no-live) cd ui && npx playwright test --grep-invert @live ;;
  *) echo "usage: $0 [smoke|ui|api|live|no-live]"; exit 1 ;;
esac
