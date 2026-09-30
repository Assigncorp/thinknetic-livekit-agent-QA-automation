#!/usr/bin/env bash
# `make setup` - everything a newcomer needs, in one command, from a fresh clone:
#
#   git clone https://github.com/Assigncorp/thinknetic-livekit-agent-QA-automation.git
#   cd thinknetic-livekit-agent-QA-automation && make setup
#
# 1. toolchain   uv (installed if missing), Node 20+ (installed with Homebrew on
#                macOS if missing, otherwise told how), pnpm (via corepack)
# 2. .env        created from .env.example if absent - secrets are never invented
# 3. packages    every suite's dependencies + Chromium for Playwright
# 4. proof       the checks that need no network or secrets: every test has a
#                testing type, the catalogue, the oracle, the SDK suite's data
#
# Safe to re-run: every step skips what is already in place. Makes no live call.
set -uo pipefail
cd "$(dirname "$0")/.."

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok() { printf '  ok    %s\n' "$*"; }
todo() { printf '  TODO  %s\n' "$*"; }
die() {
  printf '\n  FAILED  %s\n' "$*" >&2
  exit 1
}

say "1/4 toolchain"
command -v git >/dev/null || die "git is missing - install it first (https://git-scm.com/downloads)"
ok "git $(git --version | awk '{print $3}')"

if ! command -v python3 >/dev/null; then
  die "python3 is missing - install Python 3.11+ (https://www.python.org/downloads/)"
fi
ok "python3 $(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"

if ! command -v uv >/dev/null; then
  echo "  uv is missing - installing it with the official installer (https://docs.astral.sh/uv/)"
  curl -LsSf https://astral.sh/uv/install.sh | sh || die "uv install failed"
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null || die "uv installed but not on PATH - open a new terminal and re-run make setup"
fi
ok "uv $(uv --version | awk '{print $2}')"

node_major() { node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0; }
if ! command -v node >/dev/null || [ "$(node_major)" -lt 20 ]; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null; then
    echo "  Node 20+ is missing - installing it with Homebrew"
    brew install node || die "brew install node failed"
  else
    die "Node 20+ is missing - install it from https://nodejs.org (or: nvm install 22), then re-run make setup"
  fi
fi
ok "node $(node --version)"

if ! command -v pnpm >/dev/null; then
  echo "  pnpm is missing - enabling it through corepack (ships with Node)"
  corepack enable pnpm 2>/dev/null || npm install -g pnpm || die "could not install pnpm"
fi
ok "pnpm $(pnpm --version)"

say "2/4 .env"
if [ -f .env ]; then
  ok ".env already exists - left untouched"
else
  cp .env.example .env
  ok "created .env from .env.example (points at the shared dev deployment)"
fi
missing=""
for k in LIVEKIT_URL LIVEKIT_API_KEY LIVEKIT_API_SECRET; do
  grep -Eq "^$k=.+" .env || missing="$missing $k"
done
grep -Eq "^(OPENAI|GROQ)_API_KEY=.+" .env || missing="$missing OPENAI_API_KEY(or GROQ_API_KEY)"
if [ -n "$missing" ]; then
  todo "fill in .env before the live suites:$missing - ask the team lead; never commit .env"
else
  ok "every live-suite secret is set"
fi

say "3/4 packages (every suite + Chromium) - a few minutes the first time"
make --no-print-directory install || die "make install failed - see the output above"
if [ "$(uname)" = "Linux" ]; then
  (cd tests/ui && npx playwright install-deps chromium) || todo "Chromium's system libraries: run 'sudo npx playwright install-deps chromium' in tests/ui"
fi
ok "dependencies installed"

say "4/4 proof - offline checks, no network, no secrets"
failed=""
for t in check-types catalog judge-offline livekit-offline; do
  if make --no-print-directory "$t" >/dev/null 2>&1; then ok "make $t"; else failed="$failed $t"; printf '  FAIL  make %s\n' "$t"; fi
done
[ -z "$failed" ] || die "offline checks failed:$failed - run 'make$failed' to see why"

cat <<'EOF'

Ready. Next:
  make smoke            ~15 s   does the product page load? (browser, no agent call)
  make demo-livekit     ~2 min  one real call over the LiveKit SDK, verdict printed live
  make livekit-sdk      ~35 min the whole LiveKit SDK suite, in parallel
  make all-parallel     ~40 min everything
  make report-all               open report/index.html
Every command: README.md -> Command reference.
EOF
