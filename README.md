# thinknetic-livekit-agent-QA-automation

Black-box QA automation for the Thinknetic-powered Etnyre product support agent.
Runs locally against the deployed dev environment. **No application code is
modified, forked, mocked or instrumented** — the deployment is treated as an
opaque system under test, exactly as a real caller sees it.

**Target:** `https://etnyre-dev.thinknetic.app/e/products/chip-spreader`
**Mode:** text (chat) — audio is phase 2.

---

## Step-by-step setup & execution

Follow these in order on a fresh machine. Every command runs from the repo root
unless a step says otherwise.

### Step 1 — Install prerequisites

| Tool | Required version | Check with | Install |
|---|---|---|---|
| Node.js | 20+ | `node -v` | https://nodejs.org (or `nvm install 20`) |
| Python | 3.11+ | `python3 --version` | https://www.python.org/downloads/ |
| uv | any | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh`, then restart your shell |
| git | any | `git --version` | https://git-scm.com |

`npm` ships with Node, so nothing extra is needed for the UI suite. `pnpm` is
optional — `make install` uses it automatically if it's on your `PATH`, and
falls back to `npm` otherwise.

### Step 2 — Clone the repo

```bash
git clone https://github.com/Assigncorp/thinknetic-livekit-agent-QA-automation.git
cd thinknetic-livekit-agent-QA-automation
```

Skip this if you already have the repo checked out.

### Step 3 — Configure your environment

```bash
cp .env.example .env
```

The defaults already point at the shared dev deployment, so no edits are
required to get started. Open `.env` later only if you need to point at a
different environment or add LiveKit credentials for the phase-2 voice suite.

### Step 4 — Verify your toolchain

```bash
./scripts/check-env.sh
```

Confirms Node, Python, uv, git and `.env` are all in place, and tells you
exactly what's missing before you waste time on a failing install.

### Step 5 — Install dependencies

```bash
make install
```

Installs the UI's npm/pnpm packages and the Chromium browser Playwright drives,
plus the `api` and `tools` Python environments via `uv`.

### Step 6 — (Optional) Rebuild generated test resources

```bash
make resources
```

Not needed on a fresh clone — `resources/generated/*.json` is already checked
in. Run this only after editing `config/testbed.config.json`, a knowledge-base
markdown file, or the serial workbook.

### Step 7 — Know the test categories

Every UI test belongs to exactly one category, applied as a Playwright tag on
its `describe` block so it can be run standalone, filtered in CI, or combined
with others. This is the mapping the remaining steps walk through in order,
cheapest and most stable first:

| Category | Tag | Folder | Run standalone with |
|---|---|---|---|
| Smoke | `@smoke` | `tests/smoke` | `make smoke` |
| Regression | `@regression` | `tests/functional` | `make regression` |
| Negative | `@negative` | `tests/negative` | `make negative` |
| Chat (live E2E) | `@live` `@chat` | `tests/chat` | `make chat` |

- **Smoke** — must pass before anything else is worth running: page loads,
  hydrates, renders no console errors, exposes the agent entry point.
- **Regression** — the product-content and agent-session-lifecycle checks that
  guard against feature breakage; run these on every change.
- **Negative** — fail-closed behaviour: bad routes, unknown products, and the
  documented API error shape.
- **Chat** — the real caller workflow end to end, against a live agent
  session. Slowest and the only category that talks to LiveKit.

Any category can also be run directly with Playwright's own tag filter, e.g.
`npx playwright test --grep @regression`, or excluded with `--grep-invert`.

### Step 8 — Run the scenario catalogue

```bash
make catalog
```

The fastest sanity check: under a second, no browser, no network calls.
Validates that the test data itself (KB routing, serials, scenarios) is sound
before anything more expensive runs.

### Step 9 — Run the API suite

```bash
make api
```

Hits the live public API of the dev deployment directly and checks the
response contract — confirms the backend is healthy before trusting any
browser-based result.

### Step 10 — Run the smoke suite

```bash
make smoke
```

~15 seconds. Confirms the product page loads, hydrates, and the agent entry
point renders. Category: `@smoke`.

### Step 11 — Run the regression suite

```bash
make regression
```

Product content and agent-session-lifecycle checks. Category: `@regression`.

### Step 12 — Run the negative suite

```bash
make negative
```

Confirms bad routes and unknown products fail closed the way they should.
Category: `@negative`.

### Step 13 — Run the full UI suite (no live sessions)

```bash
make ui
```

Everything browser-based except tests that open a real agent session —
smoke + regression + negative in one run.

### Step 14 — Run the live chat flow suite

```bash
make chat
```

The real thing: opens live sessions against the deployed agent and drives the
full caller workflow — identify the machine, ask a question, get an answer.
Category: `@chat`.

### Step 15 — View the test report

```bash
make report
```

Opens the most recent Playwright HTML report in your browser.

### Step 16 — (Optional) Clean up test output

```bash
make clean
```

Removes local test artifacts and reports so the next run starts fresh.

> Steps 8–14 can also be run together with `make test` (api + ui, no live
> sessions). See [Commands](#commands) below for the full list.

---

## Pointing this at another product

This is a base suite. Testing a second product is a config file and a `.env`
edit — no code changes, and no forking.

```bash
cp config/testbed.config.json config/roller.config.json   # 1. describe it
$EDITOR config/roller.config.json                         #    KBs, serials, contract
$EDITOR .env                                              # 2. point at it
make resources && make chat                               # 3. run
```

`.env` carries the target and which config to use:

```bash
BASE_URL=https://other-dev.thinknetic.app
ORG_SLUG=acme
PRODUCT_SLUG=roller
TESTBED_CONFIG=config/roller.config.json
```

All three toolchains — Playwright, pytest and the resource builder — read
`TESTBED_CONFIG` from that one `.env`, so they can never end up describing
different products.

| What changes per product | Where |
|---|---|
| Target URL, org, product slug, page title | `.env` |
| Which config file describes it | `.env` → `TESTBED_CONFIG` |
| Knowledge bases, serial routing, scenario extraction | its config file |
| The conversation contract (`chatFlow.intents`) | its config file |
| KB markdown, serial workbook | its own folders under `resources/` |
| Budgets, assertion strictness, scenario seed | config file, overridable from `.env` |

Give each product its own `resources.generatedDir` in its config so their
generated files do not collide — and run `make resources` after switching, or the
catalogue suite will (correctly) fail, telling you the generated data belongs to a
different config.

Anything in the config can be overridden from `.env` for a single run without
editing the committed file — useful for a slower environment or a stricter
gate. See [`.env.example`](.env.example) for the full list.

---

## One file configures everything

The config named by `TESTBED_CONFIG` (default **`config/testbed.config.json`**) is the
single source of truth for the product under test. Which KB files exist, where the
serial list lives, how a serial routes to a knowledge base, how a scenario is picked,
what the agent's conversation contract is, every latency budget, and how strictly a
reply is judged — all declared there. No test file needs editing to change any of it.

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

`.env` holds the target, which config to load, and secrets. Everything structural is in
the config — though any budget, assertion toggle or scenario seed can be overridden
from `.env` for one run without editing the committed file.

---

## Managing resources (KB files, serials, scenarios)

Everything the agent test bed reads lives under `resources/` — nothing there is code.

```
resources/
├── kb/                          knowledge bases the agent is grounded on
│   ├── vhrs28.md                Variable hopper, RC-28   (anchor serial K7170)
│   ├── vhrs36.md                Variable hopper, RC-36   (anchor serial K6757)
│   ├── fhrc28.md                Fixed hopper,    RC-28   (anchor serial K7174)
│   ├── fhrc36.md                Fixed hopper,    RC-36   (anchor serial K6758)
│   └── troubleshooting-general.md   shared M-218-08R guide, no serial of its own
│
├── serials/
│   └── hopper-classification.xlsx   the serial list (Parent Part Numbers)
│
└── generated/                   DO NOT EDIT - rebuilt by `make resources`
    ├── serial-index.json        serial -> knowledge base
    └── scenarios.json           caller questions extracted from each KB
```

### Renaming or adding a file

Nothing reads these paths directly. Edit **`config/testbed.config.json`** and run
`make resources`:

```jsonc
"knowledgeBases": [
  { "id": "vhrs28", "file": "vhrs28.md", "controller": "RC28", "hopperType": "VARIABLE",
    "anchorSerial": "K7170", "enabled": true }
]
```

- **Renamed a KB file?** change `file`.
- **Added a fifth machine?** add an entry with its `controller` + `hopperType`; the
  serial index routes to it automatically from the workbook.
- **Retiring one temporarily?** set `enabled: false` — no files need moving.

### How a serial finds its knowledge base

The workbook's `*_Classified` sheets label each Parent Part Number `VARIABLE` or
`FIXED`. The sheet it sits on gives the controller family (RC28 or RC36). Those two
facts together pick the KB:

| Controller | Hopper | Knowledge base |
|---|---|---|
| RC28 | VARIABLE | `vhrs28` |
| RC36 | VARIABLE | `vhrs36` |
| RC28 | FIXED | `fhrc28` |
| RC36 | FIXED | `fhrc36` |

That is what makes serial rotation possible — roughly 950 classified part numbers
are usable, not just the four anchors.

### Scenario extraction

Three shapes are recognised in the KB markdown, all declared as regexes in the config:

| Pattern | Source | Becomes |
|---|---|---|
| `**Q: ...**` | FAQ sections | a direct caller question |
| `### Q: ...` | how-to / troubleshooting entries | a direct caller question |
| `## Problem N — ...` | general troubleshooting guide | the entry's `**Symptoms:**` line, i.e. what a caller would actually say |

Each scenario also carries `expectAnchors` — hard facts lifted from the KB's own answer:
part numbers, pin references, and measurements with units (`1000 PSI`, `96 RPM`,
`240°F`, `1/16"`). Ordinary vocabulary is deliberately excluded, because a term like
"switch" appears in any plausible reply and would make the check unfalsifiable. 118 of
the 221 scenarios carry at least one.

They are **not asserted by default** — see known gap 5 for the evidence. Set
`CHECK_EXPECTED_ANCHORS=true` to switch content checking on; the draw is then
restricted to anchored scenarios so a run cannot silently skip the check.

---

## Voice suite (phase 2/3)

Not active yet — `voice/` exists so the structure is settled before the work starts.

### Why it bypasses the browser

Driving voice through Playwright means fake audio devices, browser autoplay policy and
WebRTC internals all sit between you and the agent. With `LIVEKIT_URL` + API key/secret
you mint your own token, join the room as a participant, publish a WAV and subscribe to
the agent's track directly. Deterministic, headless, and roughly an order of magnitude
faster.

The browser suite still owns one thing the SDK cannot see: whether a real user can
actually start a session from the page. That stays in `ui/tests/functional/agent-entry.spec.ts`.

### What goes here when it is switched on

| Concern | Approach |
|---|---|
| Connection integrity | join, publish, subscribe, reconnect after a forced drop |
| Turn-taking | `webrtcvad` on the agent track - detect speech onset/offset boundaries |
| Latency | time from end-of-user-speech to first agent audio frame, per component budget |
| Content correctness | `faster-whisper` transcribes the agent track locally, then deterministic checks |
| Barge-in | publish over the agent mid-utterance, assert it yields |

### Setup when the time comes

```bash
cd voice
uv sync --extra live
# fill LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in the repo-root .env
uv run pytest -v
```

Put reference caller audio in `voice/fixtures/` as **16 kHz, mono, 16-bit PCM WAV**,
named after the case it drives (e.g. `FUNC-001-hopper-capacity.wav`, matching the IDs
in `/testdata/prompts/functional-queries.json`). Keep clips short — four seconds is
plenty for a turn-taking assertion — and never commit recordings of real customer calls.

---

## Folder structure

```
thinknetic-livekit-agent-QA-automation/
│
├── config/testbed.config.json  ★ SINGLE SOURCE OF TRUTH — read this first
├── .env.example                target URL and secrets only
├── Makefile                    one front door for both toolchains
│
├── resources/                  everything the test bed reads; no code — see
│   │                            "Managing resources" above for how renaming/routing work
│   ├── kb/                     vhrs28, vhrs36, fhrc28, fhrc36, troubleshooting-general
│   ├── serials/                hopper-classification.xlsx (the serial list)
│   └── generated/              serial-index.json + scenarios.json  (make resources)
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

`make chat`. Holds a real caller conversation, which normally goes:

| # | Step |
|---|---|
| 1 | click **Talk to me**, panel reaches `Listening — go ahead` |
| 2 | agent greets and asks for the serial number |
| 3 | send a serial drawn from the rotation pool |
| 4 | agent reads it back digit by digit — **confirmation is required before it will take a question** |
| 5 | confirm |
| 6 | ask a question drawn at random from that machine's KB |
| 7 | assert the answer: non-empty, inside budget, and citing a fact from that KB entry |
| 8 | end the session |

**The caller's side is not scripted.** The agent is an LLM and departs from that
shape constantly — it re-asks for a serial it dropped, answers a question with a
question, or opens with a summary of a previous session. So the suite waits for each
agent turn to *finish streaming*, reads it, matches it against the intents declared in
`chatFlow.intents`, and answers whatever was actually asked. Teaching it a new agent
behaviour means adding an intent to the config, not editing a test.

**Step 6 is a walkthrough, not an answer.** Verified live: the agent replies with a
safety preamble, offers to *text* you the steps, and — if asked to answer in the chat
— delivers the procedure one step at a time, waiting for you to confirm each one. The
manual's facts are several steps in, so the suite plays a caller who performs each
step and checks the answer against everything the agent said, not one turn. Full
detail in [`docs/chat-flow.md`](docs/chat-flow.md).

221 scenarios across the five KBs, 100 serials across the four machine families.
Full detail, including the six agent behaviours that shape the design:
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
5. **Content correctness is not asserted, and cannot be today.** The agent does not
   answer a KB question directly — it asks a clarifying question, reads a safety
   preamble, then walks the procedure one step at a time, so the manual's numbers
   arrive later than any bounded conversation reaches. `checkExpectedAnchors` ships
   **off** for that reason: left on it passes or fails depending on which scenario the
   draw picks, and a flaky gate gets ignored. The machinery is all built and tested —
   hard-fact anchors, a matcher that accepts the spoken form ("four hundred feet per
   minute" for `400 FPM`), and a draw restricted to the 118 of 221 scenarios carrying
   a checkable fact. Set `CHECK_EXPECTED_ANCHORS=true` to audit content deliberately,
   or once the agent answers inline. `failOnWrongControllerFamily` is also off — it
   targets cross-contamination between machine families, the defect that would
   actually mislead an operator.
6. **The agent does not always register the serial.** Observed on etnyre-dev
   2026-09-17: the same serial that worked minutes earlier was ignored twice in a row,
   with the agent re-asking for it instead of reading it back. The reactive driver
   answers the re-ask, so the call still completes — but a serial the agent ignores
   repeatedly will exhaust the turn budget and go red, which is the correct outcome.
7. **DEFECT — the agent never asks the caller to rate the call.** Confirmed across
   every recorded session, including the agent's own wrap-up and an explicit
   "that is all, goodbye". The `asksForFeedback` intent has never once fired.

   The suite **never volunteers a rating** — a caller who rates a call unprompted is
   not realistic, and doing so would paper over the defect. It listens, answers if
   asked, and **fails the run when it is not asked** (`assertions.requireFeedbackRequest`).

   > **`make chat` is red by design until this is fixed.** The failure is the bug
   > report: it names the defect, and the run still ends with a cleanly closed
   > session and a full transcript, because the assertion runs after teardown. The
   > moment the agent starts asking, it goes green on its own. To silence it while
   > working on something else: `REQUIRE_FEEDBACK_REQUEST=false`.

   Capturing the call reference from `/e/call-logs` to attach to the bug report is
   **blocked** — that page is behind an email magic-link login, so it needs a saved
   session, a readable test mailbox, or an API token.

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

This repo keeps a single README — everything that used to live in per-folder
`README.md` files (`resources/`, `voice/`, `voice/fixtures/`) is folded into the
sections above. `docs/` holds documents that go deeper than a README should:

| Document | Read it when |
|---|---|
| [docs/chat-flow.md](docs/chat-flow.md) | You are working on the agent conversation suite |
| [docs/architecture.md](docs/architecture.md) | You want to know why the suite is shaped this way |
| [docs/test-plan.md](docs/test-plan.md) | You need the coverage matrix or risk ranking |
| [docs/how-to-add-a-test.md](docs/how-to-add-a-test.md) | You are writing your first test here |
| [docs/locator-strategy.md](docs/locator-strategy.md) | A selector broke |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Something failed and you want the likely cause |
