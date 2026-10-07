# Code inventory

What is in this repository, what each part does, how to run it, and how it was validated.
Snapshot of 2026-09-28 (branch `develop`, uncommitted work included). For the reasoning
behind the design, follow the links; this page is the map.

**At a glance:** 4 test suites in 2 languages, **332 tests**, ~12,400 lines of test code, one
shared config file, and one deterministic knowledge-base oracle that every suite scores with.

| Suite | Language | Tests | What it tests | Needs |
|---|---|---|---|---|
| `tests/ui/` | TypeScript, Playwright | 38 | the product page, the caller form, the browser's call, the chat workflow | network |
| `tests/api/` | Python, pytest + httpx | 98 | public API contract, rate limiter, latency/payload budgets, scenario catalogue | network (catalogue: none) |
| `tests/sdk/` | Python, pytest + LiveKit SDK | 110 | real calls without a browser: session, auth, conversation, **KB grounding**, voice, concurrency | network; `LIVEKIT_*` only for auth + server-side checks |
| `tests/judge/` | Python, pytest | 86 | the deterministic oracle, KB slicing, rubrics, the optional LLM judge | none (LLM judge: `ANTHROPIC_API_KEY`) |

```
config/testbed.config.json ──► every suite reads it (KBs, serials, intents, budgets, traps, gates)
resources/kb/*.md ──make resources──► resources/generated/*.json ──► oracle index, scenarios, serials
                                                                        │
   tests/ui/ (browser)  ──recording──┐                                        ▼
   tests/sdk/ (LiveKit) ──recording──┴──► report/data/recordings/*.json ──► tests/judge/src/oracle.py ──► verdict
```

---

## 1. Shared configuration and data

| Path | Lines | What it is |
|---|---|---|
| `config/test-types.json` | — | **New.** Every test's testing type (positive / negative / edge / security / nonfunctional), as ordered test-id patterns per suite. `make test-type TYPE=…`, `make check-types`. |
| `config/testbed.config.json` | 884 | **Single source of truth.** Knowledge bases, serial routing, scenario selection, caller intake pools, the conversation contract (`chatFlow.intents`), budgets, rate-limit contract, perf budgets, judge rubrics, oracle phrase lists and gates, and the `livekitSdk` block (budgets, grounding policy, traps, probe behaviour, report-only gates). Every value carries a `_note` saying where it came from. |
| `resources/kb/*.md` | 6,791 | The five knowledge bases: `vhrs28`, `vhrs36`, `fhrc28`, `fhrc36`, `troubleshooting-general`. |
| `resources/serials/hopper-classification.xlsx` | — | The serial workbook; routes a serial to a KB. |
| `resources/generated/` | 11,677 | Built by `make resources`, never hand-edited: `serial-index.json`, `scenarios.json` (221 scenarios), `oracle.json` (per-scenario anchors, step order, safety, escalation), `corpus-numerals.json` (every legitimate figure per KB), `differential-index.json` (figures that belong to *other* machines). |
| `tools/build_resources.py`, `tools/oracle_build.py` | 657 | The generators behind `resources/generated/`. |
| `tools/check_test_types.py` | — | `make check-types` for the browser suite: every Playwright test has exactly one type tag. |
| `tools/build_report.py` | — | `make report-html`: merges every suite's JUnit XML, Playwright JSON, the KB-correctness table, LiveKit findings and oracle verdicts into **one self-contained `report/index.html`** (light/dark, filterable). Stdlib only. |
| `resources/testdata/products.json` | 20 | Invalid product routes for the fail-closed browser tests. |
| `.env.example` | 147 | Every environment variable, documented. `.env` itself is gitignored. |

## 2. `tests/ui/` — browser suite (Playwright + TypeScript)

| Path | What it does |
|---|---|
| `src/selectors.ts` | Every locator in one file (role/text based; the app has no test ids). |
| `src/pages/` | Page objects: `ProductPage` (open, caller form, start call), `ChatWidget` (transcript reader, intent-driven `converse()`, wrap-up), `VoiceWidget`, `BasePage`. |
| `src/config/` | `env.ts` (URLs, routes), `testbed.ts` (config loader with `.env` overrides, scenario/serial/caller pickers). |
| `src/fixtures/test.ts` | Fixtures: page objects, console-error capture, websocket capture, per-call room reference attached to every failure. |
| `src/utils/anchors.ts` | KB fact matcher (digits and spoken numbers) — kept in step with `tests/judge/src/anchors.py`. |
| `src/utils/session.ts` | Reads the call's room/identity from the session token for bug reports. |
| `src/utils/livekitServer.ts` | **New.** Read-only LiveKit server view (participants, tracks, room existence). |
| `src/utils/recording.ts` | **New.** Writes browser calls in the judge's transcript schema, so the oracle scores them. |

| Spec | Tag | Tests | Covers |
|---|---|---|---|
| `tests/smoke/product-page.spec.ts` | `@smoke` | 3 | page loads, hydrates, no console errors, entry point |
| `tests/functional/product-content.spec.ts` | `@regression` | 4 | product content vs the public API payload |
| `tests/functional/agent-entry.spec.ts` | `@live @regression` | 4 | caller form, panel opens, live mic mutes, realtime connection |
| `tests/functional/caller-intake-phone.spec.ts` | `@regression` | 10 | **New.** Phone requirement (US ± +1), pasted vs typed; 6 defects pinned as `test.fail` |
| `tests/negative/invalid-routes.spec.ts` | `@negative` | 3 | bad routes, unknown products |
| `tests/negative/session-fail-closed.spec.ts` | `@negative` | 4 | **New.** 500, 429, bad token, LiveKit unreachable → error + "Start again", no hang |
| `tests/chat/agent-chat-flow.spec.ts` | `@live @chat` | 6 | the full caller workflow (decline/accept the texted steps) + machine identified per KB; now writes recordings |
| `tests/unit/transcript-reader.spec.ts` | `@unit` | 2 | **New.** The transcript reader against the old and the v0.0.19 panel markup — no site, no session |
| `tests/livekit/browser-livekit.spec.ts` | `@live @livekit` | 2 | **New.** BLK-01..06: session request = form, token dispatch, agent in the page's room, **mic muted at the SFU**, End empties the room, network drop recovers or ends |

## 3. `tests/api/` — API suite (pytest + httpx)

| Path | What it does |
|---|---|
| `src/clients/product_client.py` | Public product API client. |
| `src/utils/ratelimit.py` | Reads `x-ratelimit-*`; `Bucket` parks the suite before it spends the shared 100/min window. |
| `src/utils/perf.py` | Latency/payload sampling and budget checks. |
| `tests/test_public_product.py`, `test_product_schema.py`, `test_runtime_config.py` | Endpoint contract, JSON schema, `/env.js`. |
| `tests/test_rate_limit.py` | Rate-limiter contract (`@ratelimit`); opt-in saturation (`@load`). |
| `tests/test_performance.py` | Latency and payload budgets (`@perf`), writes `report/data/api-perf.json`. |
| `tests/test_scenario_catalog.py` | The scenario catalogue — no network, <1s. Includes the phone-format guard (now 10 bare digits). |

## 4. `tests/sdk/` — LiveKit SDK suite (new)

Full design: [livekit-sdk-testing.md](livekit-sdk-testing.md). Demo: [demo-runbook.md](demo-runbook.md).

| Module | Lines | What it does |
|---|---|---|
| `lkqa/session.py` | 239 | Gets a call **the way the page does** (POST `assistant-session`); decodes token claims; rate-limit aware; mints and tampers tokens for the auth tests. |
| `lkqa/call.py` | 531 | One call: agent join, `lk.agent.state` timeline, one `lk.transcription` stream = one turn, intent-driven `converse()` and `wrap_up()`, spoken questions, transcript export. |
| `lkqa/audio.py` | 165 | Agent audio energy per frame (+ PCM for STT); a caller microphone that plays WAVs in real time. |
| `lkqa/grounding.py` | 257 | Oracle verdicts → zero-tolerance failures, coverage, planted-figure handling, **probe behaviour** (not_in_kb, off_topic, false_premise, injection, unsafe, emergency). |
| `lkqa/cases.py` | 173 | Scenario/serial/caller draws (only from machines that have eligible scenarios); the differential pair; the shared question for concurrency. |
| `lkqa/driver.py` | 111 | `scored_call()`: session → conversation → recording → verdict → report, printing the dialogue live. |
| `lkqa/admin.py` | 91 | Server view: participants, dispatches, room close. |
| `lkqa/report.py` | 60 | `report/data/livekit-sdk.*.json` (timings, findings) and `report/data/recordings/`. |
| `lkqa/llm.py` | — | **New.** Free hosted LLM (Groq / Gemini) over the OpenAI-compatible API, stdlib only; JSON replies, 429 back-off, clear skip reason without a key. |
| `lkqa/interview.py` | — | **New.** The adaptive interview: KB split into entries, passages chosen from the agent's last answer, LLM question writer with a verbatim-quote check, the auditor-rubric judge with evidence validation, the oracle half. |
| `lkqa/bridge.py` | 30 | Imports the judge's oracle and transcript model — one verdict implementation. |
| `fixtures/*.wav`, `make_fixtures.sh` | — | Caller audio (fan-valve question, barge-in), generated with macOS `say`. |

| Test file | Marker | Tests | IDs |
|---|---|---|---|
| `test_offline.py` | `offline` | 41 | SDK-OFF-01..26: traps really absent from the KB, planted figures really false, fixtures playable, every check proven able to fail, the conversation-contract order |
| `test_session_contract.py` | `contract` | 20 | LKT-01/02/04/09, SES-PH-01/02 (phone ± +1), SES-VAL-01/02, RES-09 |
| `test_auth.py` | `auth` | 8 | wrong secret, expired, no roomJoin, retargeted room, rewritten dispatch — refused; LKT-03 wrong agent name; no auto-dispatch |
| `test_conversation.py` | `live` | 17 | one full call: join, greeting by name, machine from serial, turns final, state machine, KB answer, goodbye, agent leaves, room closes |
| `test_grounding.py` | `grounding` | 12 | per-machine matrix + walkthrough, XFM-05 differential, FAB-03 ×2, FAB-05, FAB-06, RES-06, SAF-04, SAF-05 |
| `test_voice.py` | `voice` | 7 | VOI-01..05, TRN-10 barge-in |
| `test_resilience.py` | `live`/`slow` | 4 | RES-09 unknown serial, TRN-05 mid-stream message, RES-01 idle caller, MEM-01/02 returning caller |
| `test_concurrency.py` | `concurrency` | 1 | LKT-07: 3 parallel callers on 3 machines, no cross-talk |
| `test_interview.py` | `interview` | 1 | INT-01: LLM-written KB follow-up questions on one live call per machine, each answer judged by the oracle and the LLM |
| `test_kb_correctness.py` | `kbrun` | 1 | KB-RUN: every anchored FAQ + one procedure per machine + general problems on live calls, one results table |

## 5. `tests/judge/` — oracle and semantic scoring

| Path | What it does |
|---|---|
| `src/oracle.py` | **The deterministic KB verdict**: numericProvenance, unitConsistency, partProvenance, crossFamilyForbidden, requiredAnchors, stepSequence, safetyPreamble, escalation, refusalOnUnknown, applicability, k-run aggregate. |
| `src/numerals.py` | Text → (value, unit), digits and spoken forms. |
| `src/anchors.py` | KB fact matcher (Python twin of `anchors.ts`). |
| `src/corpus.py` | Slices a KB down to the section a question came from. |
| `src/scorer.py`, `src/report.py` | Optional LLM judge (report-only) and its report. |
| `src/transcript.py` | `Turn` / `Transcript` — the recording schema all suites share. |
| `src/livekit_probe.py` | `make probe-agent`: asks the deployment which agent joins. |
| `src/oracle_cli.py` | `make oracle`: scores a directory of recordings. |
| `src/testbed.py` | Config loader; now points OpenSSL at `certifi` (python.org macOS fix). |
| `tests/` | ORC-01..12 oracle suite, rubric catalogue, judge agreement, recorded calls. |
| `recordings/` | Three synthetic recordings (faithful, defective, fabricated) — the oracle's own fixtures. |

## 6. Automation, CI and docs

| Path | What it does |
|---|---|
| `Makefile` | One front door. `make all` runs every suite in order and builds the combined report; every pytest target writes `report/data/junit/<target>.xml`. New: `install-sdk`, `livekit-*` (offline, contract, auth, conversation, grounding, voice, resilience, concurrency, browser), `livekit`, `livekit-report`, `demo-livekit`; `voice` now aliases `livekit-voice`; `oracle DIR=` resolves from the repo root. |
| `.github/workflows/ci.yml` | offline job (catalogue, judge + oracle, **sdk offline**) → api → **livekit-contract** + ui (non-live). |
| `.github/workflows/perf.yml` | Scheduled perf sampling (smoke is now `ci.yml`'s `ui: smoke` switch). |
| `tools/check-env.sh` | Toolchain + `.env` preflight (`make check`). |
| `docs/` | architecture, test-plan, chat-flow, api-test-strategy, deterministic-kb-testing, **livekit-sdk-testing**, **demo-runbook**, **code-inventory**, how-to-add-a-test, locator-strategy, troubleshooting. |

**Removed on 2026-09-28** (each confirmed to have no remaining reference first):

| Removed | Why |
|---|---|
| `voice/` | placeholder of three skipped stubs, superseded by `tests/sdk/` |
| `tests/judge/src/livekit_call.py`, `tests/judge/tests/test_live_call.py`, `make judge-live`, 8 `judge.livekit` config keys | a second, weaker copy of what `tests/sdk/` does; its two contract tests moved to `tests/sdk/tests/test_offline.py` |
| `scripts/run.sh`, `scripts/setup.sh` | unreferenced wrappers duplicating `make`; `setup.sh` skipped tests/judge/sdk/tools |
| `resources/testdata/prompts/*.json`, the `products` fixture + `testData.products()` | never loaded |
| `BasePage.capture()`, `BasePage.dismissOverlays()` (empty stub), `ApiError` type | never called / never used |
| `ProductClient.get_runtime_config()`, `RateLimitState.used` / `.exhausted` | never called |
| `corpus.carries_warning`, `numerals.PHRASES_BY_LENGTH`, `test_recorded_calls._cases()` | never used |
| `sdk_cfg`, `RateLimitLow`, `ratelimit_reset`, `disconnect_reason`, `LiveKitServer.roomExists()` | unused leftovers in the new code |

---

## 7. What changed in this session (2026-09-28)

| Change | Why |
|---|---|
| Real agent name `thinknetic-agents-nonprod`, read off a live session | the configured `etnyre-support` was a guess no worker owns |
| Sessions via the public `assistant-session` endpoint (token carries the dispatch) | how the page actually does it; own-minted dispatch sent metadata the product never sends |
| Phone format → 10 bare digits (`{{area}}55501{{line}}`) | the field changed to `maxLength=10`; the old dashed format broke `make chat` and `make demo` |
| `certifi` in `tests/judge/` and `tests/sdk/` | python.org macOS Python ships no CA bundle → `CERTIFICATE_VERIFY_FAILED` |
| `chatFlow.intents`: new verified phrasings for `offersToText`, `stepwiseWalkthrough` | observed live; unmatched, they derailed the conversation |
| `ChatWidget` transcript reader walks through wrapper elements | app v0.0.19 nested the message list one Box deeper; the old reader read zero turns, so `make chat` / `make demo` never asked their question |
| The whole `tests/sdk/` suite, 5 new Playwright specs, recording writer, docs | the demo and the coverage asked for |

## 8. Validation status — 2026-09-28, against etnyre-dev

Everything below was run for real today; nothing is inferred.

**No network needed**

| Run | Result |
|---|---|
| `make catalog` | 64 passed, 1 skipped (`checkExpectedAnchors` off by design) |
| `make judge-offline` (includes the oracle's ORC-01..12) | 81 passed |
| `make livekit-offline` | 41 passed |
| `tsc --noEmit` (ui) | clean |
| `make oracle DIR=report/data/recordings` | 20 real calls re-scored offline; verdicts reproducible |

**Network, no agent session**

| Run | Result |
|---|---|
| `make api` | 92 passed, 2 skipped (both report-only config switches) |
| `make livekit-contract` | 20 passed |
| `make livekit-auth` | 8 passed |
| `ui --grep-invert @live` (smoke, regression, negative, phone field, fail-closed, reader unit) | 26 passed (6 of them are pinned defects, `test.fail`) |

**Live agent sessions** (~34 used; approved: the full set plus 7 for the chat suite and demo)

| Run | Result |
|---|---|
| `test_conversation.py` — one full call, 17 assertions | 17 passed |
| Grounding matrix — 4 machines + stepwise walkthrough | 4 of 4 zero-tolerance passes; coverage reported |
| XFM-05 differential | passed on the **old** pair, which turned out to be extraction noise → selector fixed; **new pair not yet run live** |
| FAB-03 ×2, FAB-06, RES-06 | passed |
| FAB-05 off-topic | failed on a check mismatch (agent behaved correctly) → fixed, recording re-scored offline: pass |
| SAF-04 emergency, SAF-05 unsafe | **offline only** (12 pass/fail fixtures); not run live — not in the approved session budget |
| Voice VOI-01..05 | passed; TRN-10 barge-in rewritten after a skip, **not re-run live** |
| RES-09, RES-01, MEM-01/02, TRN-05 | passed (TRN-05 records a finding: a mid-speech message is dropped) |
| LKT-07 concurrency — 3 parallel calls | passed |
| `make livekit-browser` (BLK-01..06) | 2 passed |
| `make chat` — decline, accept, machine ID ×3 | 5 passed, after fixing the transcript reader for app v0.0.19 (vhrs28 machine-ID not re-run; covered by an SDK call) |

**Fixed during validation, because they were broken:** phone format (the site's field changed), TLS on python.org macOS Python, the agent name, the transcript reader (app v0.0.19 markup), three substitution bugs in the old judge caller, a draw that could pick a machine with no eligible scenario, a walkthrough stop-rule, an XFM-05 test that could pass vacuously.

**Open findings (product, not harness)** — detail in [demo-runbook.md](demo-runbook.md) §6: phone field vs requirement; caller tokens may publish any source; API/UI serial rules disagree; DTO names in 400s; 429 shows a generic error; every call is recorded; a message typed mid-speech is dropped; scenario FHRC28/36-FAQ-053 anchors are extraction noise.
