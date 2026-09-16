# Test plan and coverage matrix

Scope: the deployed Thinknetic/Etnyre product support experience at
`etnyre-dev.thinknetic.app`, tested black-box. Application code is out of scope
for modification and for white-box coverage.

## Risk ranking

What actually hurts, worst first:

| # | Risk | Impact | Covered by |
|---|---|---|---|
| 1 | Agent gives wrong technical guidance on a machine an operator is standing in front of | Safety | `voice/` + chat semantic layer — **not yet covered** |
| 2 | Agent unreachable — entry point missing or session will not connect | Support outage | `ui/tests/smoke`, `ui/tests/functional/agent-entry` |
| 3 | Agent answers for a product it has no KB for | Wrong info, quietly | `ui/tests/negative`, `api` 404 contract |
| 4 | Backend contract changes and the UI degrades silently | Broken page | `api/tests/test_product_schema` |
| 5 | Latency makes the agent unusable in the field | Abandonment | budgets in `api` + `ui`; real numbers need `voice/` |
| 6 | Config points dev at the wrong environment | Data confusion | `api/tests/test_runtime_config` |

Note the gap: risk #1 is the highest-impact item and the least covered. That is
a deliberate phasing decision, not an oversight — see `architecture.md` on
determinism.

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
| SES-01 | Session | "Talk to me" opens the panel | ui | Active, locators unverified |
| SES-02 | Session | reaches connected state, realtime socket opens | ui | Active, locators unverified |
| CHT-01 | Chat | message in, reply out | ui | Skipped — not live on dev |
| VOI-01 | Voice | agent joins room | voice | Skipped — phase 3 |
| VOI-02 | Voice | responds to published audio | voice | Skipped — phase 3 |
| VOI-03 | Voice | first-response latency budget | voice | Skipped — phase 3 |

## Explicitly out of scope for now

Visual regression, accessibility audit, mobile viewports, authenticated flows,
concurrent-call load, and cross-browser. Each is a deliberate deferral, not an
omission — add them when the phase-1 suite has been green for a fortnight and
people trust it.
