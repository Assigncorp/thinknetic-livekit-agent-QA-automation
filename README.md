# thinknetic-livekit-agent-QA-automation

Black-box QA automation for the Thinknetic-powered Etnyre product support agent.
Runs locally against the deployed dev environment. **No application code is
modified, forked, mocked or instrumented** — the deployment is treated as an
opaque system under test, exactly as a real caller sees it.

**Target:** `https://etnyre-dev.thinknetic.app/e/products/chip-spreader`
**Mode:** text (chat) — audio is phase 2.

---

## Quick start

```bash
cp .env.example .env         # defaults already point at dev
./scripts/check-env.sh       # tells you what's missing before you waste time
make install                 # node deps + chromium + python deps
make catalog                 # <1s, no browser — proves the test data is sound
make smoke                   # ~15s
make chat                    # the real thing: opens live agent sessions
```

Requires **Node 20+**, **Python 3.11+**, and **[uv](https://docs.astral.sh/uv/)**.

---

## One file configures everything

**`config/testbed.config.json`** is the single source of truth. Which KB files exist,
where the serial list lives, how a serial routes to a knowledge base, how a scenario is
picked, what the agent's conversation contract is, every latency budget, and how
strictly a reply is judged — all declared there. No test file needs editing to change
any of it.

```jsonc
"knowledgeBases": [
  { "id": "vhrs28", "file": "vhrs28.md", "controller": "RC28",
    "hopperType": "VARIABLE", "anchorSerial": "K7170", "enabled": true }
]
```

Renamed a KB? Change `file`. Added a fifth machine? Add an entry — the serial index
routes to it automatically. Retiring one? `"enabled": false`. Then:

```bash
make resources     # rebuilds resources/generated/*
```

`.env` holds only the target URL and secrets. Everything else is in the config.

---

## Folder structure

```
thinknetic-livekit-agent-QA-automation/
│
├── config/testbed.config.json  ★ SINGLE SOURCE OF TRUTH — read this first
├── .env.example                target URL and secrets only
├── Makefile                    one front door for both toolchains
│
├── resources/                  everything the test bed reads; no code
│   ├── kb/                     vhrs28, vhrs36, fhrc28, fhrc36, troubleshooting-general
│   ├── serials/                hopper-classification.xlsx (the serial list)
│   ├── generated/              serial-index.json + scenarios.json  (make resources)
│   └── README.md               how renaming and routing work
│
├── tools/build_resources.py    workbook + KB markdown → generated JSON
│
├── ui/                         BROWSER SUITE — Playwright + TypeScript   [ACTIVE]
│   ├── src/
│   │   ├── config/             env.ts (routes/API) + testbed.ts (config + pickers)
│   │   ├── constants/          timeouts and budgets
│   │   ├── selectors.ts        ★ EVERY locator lives here
│   │   ├── types/              API payload + test-bed types
│   │   ├── pages/              BasePage, ProductPage, VoiceWidget, ChatWidget
│   │   ├── fixtures/test.ts    page objects, console errors, socket capture
│   │   └── utils/              logger, test-data loader
│   └── tests/
│       ├── smoke/              must pass before anything else is worth running
│       ├── functional/         page content + session lifecycle
│       ├── negative/           bad routes, fail-closed behaviour
│       └── chat/               ★ the real caller workflow, end to end
│
├── api/                        API SUITE — pytest + httpx                [ACTIVE]
│   ├── src/{clients,schemas,utils}
│   └── tests/                  endpoint contract, JSON schema, runtime config,
│                               and the scenario catalogue (no agent calls)
│
├── voice/                      VOICE SUITE — LiveKit Python SDK          [PHASE 2]
├── scripts/                    check-env, setup, run
├── docs/                       architecture, chat-flow, test-plan, how-to-add-a-test,
│                               locator-strategy, troubleshooting
├── .github/workflows/ci.yml    catalogue → api → ui
└── reports/                    all output (gitignored)
```

---

## The two scenario suites

### 1. Catalogue suite — no calls, under a second

`make catalog` (56 checks). Validates the data the expensive suite depends on: every
declared KB file exists, serial routing is unambiguous, every anchor serial survives
regeneration, no serial routes to two KBs, every scenario is traceable to a line in its
source file, budgets are ordered sensibly, the rotation pool is big enough to be worth
rotating.

When a KB is renamed or the workbook changes, **this** goes red and names the cause —
instead of a 45-second chat test failing with "the agent did not reply".

### 2. Chat flow suite — real sessions

`make chat`. Drives the verified caller workflow:

| # | Step |
|---|---|
| 1 | click **Talk to me**, panel reaches `Listening — go ahead` |
| 2 | agent greets and asks for the serial number |
| 3 | send a serial drawn from the rotation pool |
| 4 | agent reads it back digit by digit — **confirmation is required before it will take a question** |
| 5 | confirm |
| 6 | ask a question drawn at random from that machine's KB |
| 7 | assert a non-empty answer inside budget |
| 8 | end the session |

221 scenarios across the five KBs, 100 serials across the four machine families.
Full detail, including the three agent behaviours that shape the design:
[`docs/chat-flow.md`](docs/chat-flow.md).

---

## Commands

| Command | What it does |
|---|---|
| `make catalog` | Scenario catalogue — no browser, no calls, <1s |
| `make api` | Public endpoint suite + catalogue |
| `make smoke` | Page loads, hydrates, entry point present |
| `make negative` | Bad routes, fail-closed behaviour |
| `make ui` | Full browser suite **except** live sessions |
| `make chat` | The real agent chat flow (opens live sessions) |
| `make resources` | Rebuild `resources/generated/*` after a config or KB change |
| `make test` | `api` then `ui` — no live sessions |
| `make report` | Open the last Playwright HTML report |

```bash
cd ui
npx playwright test --grep @chat          # live chat only
npx playwright test --grep-invert @live   # everything that touches no session
```

---

## Known gaps — read before trusting a green run

1. **The agent remembers previous sessions per serial.** After confirming a serial it
   may open with *"Last time, you asked me to…"*. The suite rotates serials and never
   asserts on that turn's wording, but the history still accumulates. A reset mechanism
   from the devs would make this fully repeatable.
2. **The agent injects unprompted turns** ("Are you still there?"). Filtered out by
   `chatFlow.agentIdlePrompts` before any assertion.
3. **The transcript has no roles or test ids** — speaker is inferred from layout
   alignment. See `docs/chat-flow.md` for why, and what would replace it.
4. **Budgets are placeholders**, not measurements. Collect a week of dev baselines and
   reset to ~p95.
5. **Content correctness is not asserted.** `checkExpectedAnchors` and
   `failOnWrongControllerFamily` ship switched off. The second is the higher-value one.

---

## System under test — verified 2026-09-16

| Aspect | Finding |
|---|---|
| Frontend | React + Vite SPA, MUI (Minimals template), goober |
| Data layer | TanStack Query, better-auth |
| Runtime config | `/env.js` — environment switching without a rebuild |
| Public API | `GET /api/v1/public/organizations/{org}/products/{slug}` → 200, no auth |
| Error contract | unknown product **and** unknown org → `404 {message, error, statusCode}` |
| Agent flag | `has_assistant` drives the "Talk to me" entry point |
| Session panel | text input, `Send` / `Mute` / `End`, status `Listening — go ahead` |
| Agent persona | "Jason with Etnyre Customer Support"; asks for serial, reads it back |
| Test hooks | none |

---

## Documentation

| Document | Read it when |
|---|---|
| [docs/chat-flow.md](docs/chat-flow.md) | You are working on the agent conversation suite |
| [resources/README.md](resources/README.md) | You are renaming, adding or routing a KB |
| [docs/architecture.md](docs/architecture.md) | You want to know why the suite is shaped this way |
| [docs/test-plan.md](docs/test-plan.md) | You need the coverage matrix or risk ranking |
| [docs/how-to-add-a-test.md](docs/how-to-add-a-test.md) | You are writing your first test here |
| [docs/locator-strategy.md](docs/locator-strategy.md) | A selector broke |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Something failed and you want the likely cause |
