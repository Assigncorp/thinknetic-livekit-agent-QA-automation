# Test plan and coverage matrix

Scope: the deployed Thinknetic/Etnyre product support experience at
`etnyre-dev.thinknetic.app`, tested black-box. Application code is out of scope
for modification and for white-box coverage.

## Risk ranking

What actually hurts, worst first:

| # | Risk | Impact | Covered by |
|---|---|---|---|
| 1 | Agent gives wrong technical guidance on a machine an operator is standing in front of | Safety | improving — the deterministic oracle (ORC-*) catches fabricated and cross-family figures offline; ships **report-only**, see note below |
| 2 | Agent unreachable — entry point missing or session will not connect | Support outage | `tests/ui/tests/smoke`, `tests/ui/tests/functional/agent-entry` |
| 3 | Agent answers for a product it has no KB for | Wrong info, quietly | `tests/ui/tests/negative`, `api` 404 contract |
| 4 | Backend contract changes and the UI degrades silently | Broken page | `tests/api/tests/test_product_schema` |
| 5 | Latency makes the agent unusable in the field | Abandonment | `tests/api/tests/test_performance` at the HTTP layer; budgets in `ui`; the number that matters (agent turn latency) is measured per turn by `tests/sdk/` (report/data/livekit-sdk.*.json) — see livekit-sdk-testing.md |
| 6 | Config points dev at the wrong environment | Data confusion | `tests/api/tests/test_runtime_config` |
| 7 | A client cannot back off correctly, or the limiter stops enforcing | Throttled UI, or an unprotected endpoint | `tests/api/tests/test_rate_limit` |

Note the gap, and what has changed. Risk #1 is still the highest-impact item, but it is no
longer the least covered. CHT-06/07 remain off in `config/testbed.config.json` for the
reason they always were — they produce false failures on valid paraphrases — and the
replacement for them is now built: `tests/judge/src/oracle.py` compiles the knowledge bases into
an index and asserts against it deterministically, so a fabricated specification or a
figure belonging to another machine is caught by parsing rather than by matching wording.
It runs offline on every PR (ORC-01..12) and reports on recorded calls via `make oracle`.

It ships report-only too — every entry in `config.oracle.gates` is `false`, asserted by
ORC-05 — because a gate whose threshold was read off a manual rather than measured from
calls goes red on a healthy deployment. `crossFamilyForbidden` and `numericProvenance` are
the two to switch on first, once a fortnight of nightly runs says the baseline is clean.
See [deterministic-kb-testing.md](deterministic-kb-testing.md) for the design, the full
case catalogue (LKT/TRN/DKB/FAB/XFM/SAF/MEM/CNV/RES/ORC) and the edge-case list, and
`architecture.md` on determinism.

## Coverage matrix

| ID | Area | Case | Layer | Status |
|---|---|---|---|---|
| SMK-01 | Page | loads, hydrates, entry point visible | ui | Active |
| SMK-02 | Page | no console/page errors | ui | Active |
| SMK-03 | Page | unknown slug renders no entry point | ui | Active |
| API-01 | API | product endpoint 200 + JSON | api | Active |
| API-02 | API | required fields present | api | Active |
| API-03 | API | `has_assistant` is true | api | Active |
| API-04 | API | slug echoes the request | api | Active |
| API-05 | API | assets non-empty | api | Active |
| API-06 | API | unknown product → 404 + error shape | api | Active |
| API-07 | API | unknown org → 404 | api | Active |
| API-08 | API | response inside 3s budget | api | Active |
| API-09 | API | payload matches JSON schema | api | Active |
| CFG-01 | Config | `/env.js` served | api | Active |
| CFG-02 | Config | no obvious secrets in `/env.js` | api | Active |
| RL-01 | Rate limit | API advertises its limit | api | Active |
| RL-02 | Rate limit | limit/remaining/reset internally consistent | api | Active |
| RL-03 | Rate limit | the limit has not silently changed | api | Active |
| RL-04 | Rate limit | consecutive requests decrement `remaining` | api | Active |
| RL-05 | Rate limit | a 404 still costs a request | api | Active |
| RL-06 | Rate limit | one bucket covers the whole API | api | Active |
| RL-07 | Rate limit | `/env.js` stays outside the bucket | api | Active |
| RL-11 | Rate limit | limiter state consistent across instances — **it is not** | api | Reports; off by config |
| RL-08 | Rate limit | a burst past the limit never 5xxs | api | Opt-in (`@load`) |
| RL-12 | Rate limit | the advertised limit is actually enforced — **it is not, for one client** | api | Opt-in; reports, off by config |
| RL-09 | Rate limit | the 429 tells a client how to back off | api | Opt-in (`@load`) |
| RL-10 | Rate limit | the window rolls over and service resumes | api | Opt-in (`@load`) |
| PERF-01 | Performance | first request on a fresh connection inside `coldMs` | api | Active |
| PERF-02 | Performance | warm p50 inside budget | api | Active |
| PERF-03 | Performance | warm p95 inside budget | api | Active |
| PERF-04 | Performance | no single sample breaches the 3s ceiling | api | Active |
| PERF-05 | Performance | p95/p50 spread bounded — latency not bimodal | api | Active |
| PERF-06 | Performance | payload inside its byte budget | api | Active |
| PERF-07 | Performance | compression still negotiated, ≥2× saving | api | Active |
| PERF-08 | Performance | 5 concurrent callers — endpoint does not serialise | api | Active |
| PERF-09 | Performance | 404 path no slower than the happy path | api | Active |
| PERF-10 | Performance | `/env.js` p95 — it blocks SPA boot | api | Active |
| UI-01 | Content | heading matches API `name` | ui | Active |
| UI-02 | Content | entry point matches `has_assistant` | ui | Active |
| UI-03 | Content | gallery renders assets | ui | Active |
| UI-04 | Content | lightbox opens and closes | ui | Active |
| NEG-01 | Negative | invalid routes fail closed | ui | Active |
| NEG-02 | Negative | API error shape on unknown product | ui | Active |
| SES-00 | Session | "Talk to me" opens the caller intake form; it will not submit empty | ui | Active |
| SES-01 | Session | filled intake form opens the panel | ui | Active |
| SES-02 | Session | reaches connected state, realtime socket opens | ui | Active |
| CAT-01 | Catalogue | every declared KB file exists | api | Active |
| CAT-02 | Catalogue | serial routing is unambiguous | api | Active |
| CAT-03 | Catalogue | anchor serial present and routes correctly | api | Active |
| CAT-04 | Catalogue | no serial routes to two KBs | api | Active |
| CAT-05 | Catalogue | scenario text still present in its source KB | api | Active |
| CAT-06 | Catalogue | rotation pool large enough to matter | api | Active |
| CAT-07 | Catalogue | budgets ordered sensibly | api | Active |
| CHT-01 | Chat | full positive workflow, declining the texted steps: intake form → ask → answer in chat → sign off → end | ui | Active |
| CHT-01b | Chat | full positive workflow, accepting the texted steps (agent falls back to chat: number not textable) | ui | Active |
| CHT-02 | Chat | agent greets inside budget | ui | Active |
| CHT-03 | Chat | agent confirms the machine from the form's serial, inside budget | ui | Active |
| CHT-04 | Chat | each machine family identified from its own serial (4 cases) | ui | Active |
| CHT-05 | Chat | answer is non-empty and inside budget | ui | Active |
| CHT-06 | Chat | answer contains anchors from the KB's own answer | ui | Off by config |
| CHT-07 | Chat | RC-28 serial never gets an RC-36 answer | ui | Off by config |
| CHT-08 | Chat | agent asks the caller to rate the call after they sign off | ui | Active |
| CHT-09 | Chat | caller answers the rating with a drawn score, and the agent closes the call | ui | Active |
| CAT-08 | Catalogue | generated phone numbers stay inside the fictional 555-01xx block | api | Active |
| CAT-09 | Catalogue | the sign-off never volunteers a rating | api | Active |
| CAT-10 | Catalogue | both answers to the text offer exist and interpolate only known values | api | Active |
| CAT-11 | Catalogue | specific intents outrank generic ones (ordering rules) | api | Active |
| VOI-01 | Voice | agent joins room | voice | Skipped — phase 3 |
| VOI-02 | Voice | responds to published audio | voice | Skipped — phase 3 |
| VOI-03 | Voice | first-response latency budget | voice | Skipped — phase 3 |
| JC-01 | Judge | rubrics are declared, weighted and well-formed | judge | Offline — runs on every PR |
| JC-02 | Judge | all 221 scenarios resolve to the right KB section | judge | Offline |
| JC-03 | Judge | anchor matcher agrees with `tests/ui/src/utils/anchors.ts` | judge | Offline |
| JC-04 | Judge | the prompt carries the section, the family constraint and every rubric | judge | Offline |
| JA-01 | Judge | a faithful answer scores well (no false positive on a gating rubric) | judge | Needs `ANTHROPIC_API_KEY` |
| JA-02 | Judge | a defective answer is caught — fabrication, cross-family, stripped warning | judge | Needs `ANTHROPIC_API_KEY` |
| JA-03 | Judge | the judge separates the two by ≥0.25 | judge | Needs `ANTHROPIC_API_KEY` |
| JS-01 | Judge | recorded calls scored against their KB | judge | Report-only — never gates |
| JS-02 | Judge | judge vs literal anchor-matcher disagreements | judge | Report-only |
| LK-01 | Judge | drive a real call over the LiveKit SDK, record it, score it | judge | Skipped — `LIVEKIT_*` now set; blocked on confirming `agentName` |
| ORC-01 | Oracle | spoken-number grammar round-trips with `anchors.spell_integer`; non-measurements stay non-measurements | judge | Offline — runs on every PR |
| ORC-02 | Oracle | bounded matching: `0 PSI` does not fire inside `400 PSI` | judge | Offline |
| ORC-03 | Oracle | `P1-PIN 21` compiles to a pattern that matches (silent-failure regression) | judge | Offline |
| ORC-04 | Oracle | differential index: no allowed/forbidden overlap, every figure attributed, never empty | judge | Offline |
| ORC-05 | Oracle | unit table resolves; phrase lists auditable; **every gate ships off** | judge | Offline |
| ORC-06 | Oracle | every scenario has an entry; coverage counts match; structural-only tagged | judge | Offline |
| ORC-07 | Oracle | the compiled corpus matches a fresh parse — catches a KB edited without `make resources` | judge | Offline |
| ORC-08 | Oracle | applicability: non-reaching run, SMS-accept path, reaching run | judge | Offline |
| ORC-09 | Oracle | a faithful call fails nothing (false-positive guard) | judge | Offline |
| ORC-10 | Oracle | a defective call is caught with no model; scoring is byte-identical twice | judge | Offline |
| ORC-11 | Oracle | a fabricated specification is caught, spoken as well as written | judge | Offline |
| ORC-12 | Oracle | a foreign figure is caught and attributed; a correct answer is not flagged | judge | Offline |
| FAB-01 | Oracle | every measurement in a real call traces to that machine's manual | judge | Report-only — gate candidate |
| XFM-01 | Oracle | no figure from another machine reaches this caller | judge | Report-only — gate candidate |
| SAF-01 | Oracle | the safety instruction precedes the first step fact | judge | Report-only — gate candidate |

## Explicitly out of scope for now

Visual regression, accessibility audit, mobile viewports, authenticated flows,
concurrent-call load, and cross-browser. Each is a deliberate deferral, not an
omission — add them when the phase-1 suite has been green for a fortnight and
people trust it.

Sustained-load capacity testing is out of scope for a harder reason than
priority: the API allows 100 requests a minute across the whole suite, so any
load tool would spend its run measuring the rate limiter rather than the
endpoint. [api-test-strategy.md](api-test-strategy.md) sets out what would
have to change first, and lists the rate-limit and performance cases that are
deferred (RL-11..RL-14, PERF-11..PERF-16) with the reason for each.
