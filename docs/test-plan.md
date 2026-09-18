# Test plan and coverage matrix

Scope: the deployed Thinknetic/Etnyre product support experience at
`etnyre-dev.thinknetic.app`, tested black-box. Application code is out of scope
for modification and for white-box coverage.

## Risk ranking

What actually hurts, worst first:

| # | Risk | Impact | Covered by |
|---|---|---|---|
| 1 | Agent gives wrong technical guidance on a machine an operator is standing in front of | Safety | partially — CHT-06/07 exist but ship **switched off**; see note below |
| 2 | Agent unreachable — entry point missing or session will not connect | Support outage | `ui/tests/smoke`, `ui/tests/functional/agent-entry` |
| 3 | Agent answers for a product it has no KB for | Wrong info, quietly | `ui/tests/negative`, `api` 404 contract |
| 4 | Backend contract changes and the UI degrades silently | Broken page | `api/tests/test_product_schema` |
| 5 | Latency makes the agent unusable in the field | Abandonment | budgets in `api` + `ui`; real numbers need `voice/` |
| 6 | Config points dev at the wrong environment | Data confusion | `api/tests/test_runtime_config` |

Note the gap: risk #1 is the highest-impact item and the least covered. The machinery
for it now exists — CHT-06 checks the answer against anchor terms lifted from the KB's
own answer, CHT-07 fails when an RC-28 serial gets an RC-36 answer — but both are
disabled in `config/testbed.config.json` because they will produce false failures on
valid paraphrases. Turning CHT-07 on is the highest-value next step: cross-contamination
between machine families is the defect that would actually mislead an operator, and it
is far less paraphrase-sensitive than CHT-06. See `architecture.md` on determinism.

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

## Explicitly out of scope for now

Visual regression, accessibility audit, mobile viewports, authenticated flows,
concurrent-call load, and cross-browser. Each is a deliberate deferral, not an
omission — add them when the phase-1 suite has been green for a fortnight and
people trust it.
