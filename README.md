# thinknetic-livekit-agent-QA-automation

Black-box QA automation for the Thinknetic-powered Etnyre product support agent.
Runs locally against the deployed dev environment. **No application code is
modified, forked, mocked or instrumented** — the deployment is treated as an
opaque system under test, exactly as a user or an external client sees it.

**Target:** `https://etnyre-dev.thinknetic.app/e/products/chip-spreader`

---

## Quick start

```bash
cp .env.example .env         # defaults already point at dev
./scripts/check-env.sh       # tells you what's missing before you waste time
make install                 # node deps + chromium + python deps
make smoke                   # ~15s sanity run
```

Requires **Node 20+**, **Python 3.11+**, and **[uv](https://docs.astral.sh/uv/)**.

---

## Folder structure

```
thinknetic-livekit-agent-QA-automation/
│
├── README.md                   ← you are here
├── Makefile                    one front door for both toolchains
├── .env.example                copy to .env; shared by ui/ and api/
│
├── ui/                         BROWSER SUITE — Playwright + TypeScript   [ACTIVE]
│   ├── playwright.config.ts    reporters, budgets, fake-media launch args
│   ├── src/
│   │   ├── config/env.ts       base URL, routes, API paths — no process.env elsewhere
│   │   ├── constants/          timeouts and performance budgets, all in one place
│   │   ├── selectors.ts        ★ EVERY locator lives here. See locator-strategy.md
│   │   ├── types/              typed API payloads
│   │   ├── pages/              page objects — BasePage, ProductPage, VoiceWidget, ChatWidget
│   │   ├── fixtures/test.ts    custom Playwright fixtures (page objects, console, sockets)
│   │   └── utils/              logger, shared test-data loader
│   └── tests/
│       ├── smoke/              must pass before anything else is worth running
│       ├── functional/         core behaviour + agent session lifecycle
│       ├── negative/           bad routes, fail-closed behaviour
│       └── chat/               chat mode                                [SKIPPED]
│
├── api/                        API SUITE — pytest + httpx                [ACTIVE]
│   ├── conftest.py             fixtures: client, slugs, schema
│   ├── src/
│   │   ├── clients/            ProductClient — all URL construction
│   │   ├── schemas/            JSON Schema contract for the product payload
│   │   └── utils/              shared test-data loader
│   └── tests/                  endpoint contract, error handling, runtime config
│
├── voice/                      VOICE SUITE — LiveKit Python SDK          [PHASE 3]
│   ├── README.md               why it bypasses the browser, and what goes in it
│   ├── fixtures/               reference caller audio (16 kHz mono WAV)
│   └── tests/                  scaffolded, skipped until credentials are wired
│
├── testdata/                   language-neutral fixtures, shared by all suites
│   ├── products.json           valid + invalid product/org combinations
│   └── prompts/
│       ├── functional-queries.json   questions the agent should answer
│       └── negative-queries.json     inputs it should refuse or escalate
│
├── scripts/
│   ├── check-env.sh            verify toolchain before installing
│   ├── setup.sh                one-shot setup, safe to re-run
│   └── run.sh                  ./scripts/run.sh [smoke|ui|api|live|no-live]
│
├── docs/                       architecture, test plan, how to add a test,
│                               locator strategy, troubleshooting
│
├── .github/workflows/ci.yml    api job → ui job, artefacts uploaded
└── reports/                    all output lands here (gitignored)
```

---

## Commands

| Command | What it does |
|---|---|
| `make install` | Install everything (node, chromium, python) |
| `make smoke` | Fast sanity: page loads, hydrates, entry point present |
| `make api` | Public endpoint contract, schema, error handling |
| `make ui` | Full browser functional suite |
| `make test` | `api` then `ui` |
| `make report` | Open the last Playwright HTML report |
| `make clean` | Wipe test output |

Filtering:

```bash
cd ui
npx playwright test --grep @smoke              # smoke only
npx playwright test --grep-invert @live        # skip tests that open a real agent session
npx playwright test --headed --grep @live      # watch the session tests run
```

---

## How the layers fit together

```
   ui/     what a user can see and do          slow, broad, closest to reality
   api/    what the client is served           fast, precise, cheapest signal
   voice/  what the agent actually says        phase 3
```

Cheapest signal first: CI runs the API suite before the browser suite, because a
broken payload makes every downstream browser assertion meaningless — and it
takes seconds rather than minutes to discover.

**Two languages, on purpose.** Playwright's TypeScript API has the best
auto-waiting and trace viewer for a React SPA whose agent widget mounts
asynchronously. LiveKit's usable test-harness client is Python, and the Python
audio stack (`webrtcvad`, `faster-whisper`, `soundfile`) has no real Node
equivalent. The Makefile and a shared root `.env` keep the seam out of daily use.

---

## What is covered today

| Layer | Covered | Not yet |
|---|---|---|
| Page | load, hydration against the public API, console errors, gallery, lightbox, unknown-slug | visual regression, a11y, mobile |
| Session | entry point opens a panel, reaches connected state, realtime socket opens, teardown | audio content, turn-taking, barge-in |
| API | status, required fields, JSON schema, `has_assistant`, 404 contract, latency, `/env.js` | authenticated endpoints, fuzzing |
| Chat | — | everything (widget not live on dev) |

Full matrix with IDs and risk ranking: [`docs/test-plan.md`](docs/test-plan.md).

**All assertions are deterministic** — status codes, element presence, socket
establishment, latency budgets. Nothing here scores the *wording* of an LLM
reply. That is deliberate: asserting on generated wording produces a suite that
is red every morning and that nobody trusts. Semantic scoring is a later phase
and should be threshold-based and reported separately, so a borderline score
never blocks a release on its own.

---

## The one thing to know before editing

The app under test ships **zero `data-testid` attributes**, and we cannot add
them. Every locator is therefore role- or text-based, and they **all live in
`ui/src/selectors.ts`**. A selector string in a test file is a bug in the test
file. Full reasoning and the brittleness register: [`docs/locator-strategy.md`](docs/locator-strategy.md).

---

## Known gaps — read before trusting a green run

1. **`sel.voiceWidget.*` locators are UNVERIFIED.** They were written from
   expected markup, not observed markup, because confirming them means opening a
   real agent session on the dev environment. Expect `SES-01`/`SES-02` to fail on
   the first run; the fix is one file.
2. **The 15s time-to-connected budget is a placeholder**, not a measurement.
   Collect a week of dev baselines and reset it to roughly p95.
3. **The highest-impact risk — the agent giving wrong technical guidance — is
   the least covered.** Phasing decision, documented in `docs/test-plan.md`.
4. **Authenticated flows** will hit the known better-auth cookie naming and
   URL-encoding quirk when phase 2 starts.

---

## System under test — verified 2026-09-16

| Aspect | Finding |
|---|---|
| Frontend | React + Vite SPA, MUI (Minimals template), goober |
| Data layer | TanStack Query, better-auth |
| Runtime config | `/env.js` — environment switching without a rebuild |
| Public API | `GET /api/v1/public/organizations/{org}/products/{slug}` → 200, no auth |
| Error contract | unknown product **and** unknown org → `404 {message, error, statusCode}` |
| Agent flag | `has_assistant` in the payload drives the "Talk to me" entry point |
| Test hooks | none |

---

## Documentation

| Document | Read it when |
|---|---|
| [docs/architecture.md](docs/architecture.md) | You want to know why the suite is shaped this way |
| [docs/test-plan.md](docs/test-plan.md) | You need the coverage matrix or the risk ranking |
| [docs/how-to-add-a-test.md](docs/how-to-add-a-test.md) | You are writing your first test here |
| [docs/locator-strategy.md](docs/locator-strategy.md) | A selector broke, or you are adding one |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Something failed and you want the likely cause |
