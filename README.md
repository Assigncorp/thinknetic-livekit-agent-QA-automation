# thinknetic-livekit-agent-QA-automation

Black-box QA automation for the Thinknetic-powered Etnyre product support agent.
Runs entirely locally against the deployed dev environment. **No application code
is modified, forked or instrumented** - everything here treats the deployment as
an opaque system under test.

Target: `https://etnyre-dev.thinknetic.app/e/products/chip-spreader`

## Layout

```
ui/      Playwright + TypeScript - browser functional suite       ACTIVE
api/     pytest + httpx          - public endpoint suite          ACTIVE
voice/   LiveKit Python SDK      - voice agent suite              PHASE 3 (skipped)
docs/    architecture + locator strategy
reports/ all test output lands here (gitignored)
```

Two languages on purpose: Playwright's TypeScript API is the strongest browser
story, and LiveKit's only first-class client SDK for this job is Python. The
`Makefile` hides the split behind one set of commands.

## Setup

Requires Node 20+, Python 3.11+, and [uv](https://docs.astral.sh/uv/). Then:

```bash
cp .env.example .env     # defaults already point at dev
make install             # pnpm/npm install + playwright chromium + uv sync
```

## Running

```bash
make smoke    # ~15s - page loads, hydrates, entry point present
make api      # public endpoint contract + error handling
make ui       # full browser functional suite
make test     # api then ui
make report   # open the last Playwright HTML report
```

Filter by tag: `cd ui && npx playwright test --grep @smoke`, or skip the tests
that open a real agent session with `--grep-invert @live`.

## What is covered today

| Layer | Covered | Not yet |
|---|---|---|
| Page | load, hydration against the public API, console errors, gallery, lightbox, unknown-slug handling | visual regression, a11y audit, mobile viewport |
| Session | "Talk to me" opens a panel, reaches connected state, opens a realtime socket, tears down | audio content, turn-taking, barge-in |
| API | public product endpoint status/shape/latency, 404 behaviour, `/env.js` config surface | authenticated endpoints, schema fuzzing |
| Chat | - | everything (widget not yet live on dev) |

Assertions are deterministic by design - status codes, element presence, latency
budgets, socket establishment. Nothing here scores the *wording* of an LLM reply.
That belongs in a semantic scoring layer, deliberately deferred; see
`docs/architecture.md`.

## The one thing to know before editing

The app ships **no `data-testid` attributes** and we cannot add them. Every
locator is role- or text-based and they all live in `ui/src/selectors.ts`.
Never put a raw selector in a test file. See `docs/locator-strategy.md`.
