#!/usr/bin/env bash
# One-shot local setup. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .env ]] || { cp .env.example .env; echo "created .env from .env.example"; }

echo "==> UI dependencies"
cd ui
if command -v pnpm >/dev/null 2>&1; then pnpm install; else npm install; fi
npx playwright install chromium
cd ..

echo "==> API dependencies"
cd api && uv sync && cd ..

echo
echo "Done. Try: make smoke"
