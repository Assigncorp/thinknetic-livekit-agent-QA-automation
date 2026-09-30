#!/usr/bin/env bash
# Verifies the local toolchain before anyone wastes time on a failing install.
set -uo pipefail

ok=0
check() {
  local name="$1" cmd="$2" min="$3"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "  %-12s %s\n" "$name" "$($cmd --version 2>&1 | head -1)"
  else
    printf "  %-12s MISSING (need %s)\n" "$name" "$min"
    ok=1
  fi
}

echo "Toolchain:"
check "node"   node   "20+"
check "python3" python3 "3.11+"
check "uv"     uv     "any - https://docs.astral.sh/uv/"
check "git"    git    "any"

echo
if [[ -f .env ]]; then
  echo ".env: present"
else
  echo ".env: MISSING - run: cp .env.example .env"
  ok=1
fi

echo
if [[ $ok -eq 0 ]]; then echo "Ready. Next: make install"; else echo "Fix the above, then re-run."; fi
exit $ok
