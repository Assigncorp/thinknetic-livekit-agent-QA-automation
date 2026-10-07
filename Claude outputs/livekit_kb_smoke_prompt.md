# Prompt: LiveKit KB-steps smoke test (one call, fixed flow) + CI + HTML report

You are working in the repo `thinknetic-livekit-agent-QA-automation`, branch `develop-phase1_basic`. This branch becomes our standard smoke test, so build it carefully. **Do not assume anything listed under "Open questions". Ask me those first and wait for my answers before you write code.**

## What already exists (read first)

- `tests/sdk/lkqa/call.py`: the `Call` class drives one call over the LiveKit SDK.
  - The agent joins as a `kind=AGENT` participant.
  - Each agent turn arrives as one text stream on `lk.transcription`.
  - `lk.agent.state` goes listening → thinking → speaking → listening.
  - The caller types on `lk.chat`.
  - Also defined here: `agent_token()` (token with agent dispatch and product metadata) and `is_holding()`, because a "let me check" turn is not the answer.
- `tests/sdk/tests/test_basic_call.py`: the current single flow (greeting → serial/read-back → question → answer). The caller reacts to what the agent says instead of following a fixed script. Reuse this turn-reading logic. Do not rewrite it from scratch.
- `tests/sdk/conftest.py`: `product`, `caller` and `question` fixtures, plus `.env` loading.
- `tests/ui/`: Playwright (TypeScript, pnpm) product-page UI test. Its HTML report goes to `report/playwright`.
- `Makefile`: `make test` runs the UI test first, then the SDK test. If the UI test fails, the run stops.
- `report/`: output folder.
- `.env.example`: LIVEKIT_*, AGENT_NAME, TEST_*, product metadata.

## Knowledge base (source of truth for questions and validation)

Four KB files are attached. Copy them unchanged into `kb/` in the repo:

| File | Model |
|---|---|
| `2026-08-07-vhrs28-voice-agent-knowledge-base.md` | VHRS28: variable-width hopper, 28" |
| `2026-08-07-vhrs36-voice-agent-knowledge-base.md` | VHRS36: variable hopper, 36" (S/N K6975 and up) |
| `2026-08-17-FHRC36-VoiceAgent-Knowledge-Base.md` | FHRC36: fixed hopper, RC-36 controller |
| `2026-09-24-fhrc28-voice-agent-knowledge-base.md` | FHRC28: fixed hopper, RC-28 controller |

How these files are structured:

- Procedures are `###` sections with numbered steps. Troubleshooting entries are `### Q: …` with ordered checks.
- Cautions appear in several forms. The extractor must handle all of them:
  - block quotes: `> **WARNING:** …` / `> **CAUTION:** …`
  - inline: `**Warning:** …` / `**Caution:** …`
  - nested under a step: `   > **CAUTION:** …`
  - inside a step's own text: "Do NOT crank for more than 30 seconds…"

### Serial → model routing: `kb/hopper_classification.xlsx` (attached; copy it in unchanged)

The workbook decides which KB applies to a serial. The routing rule:

| Sheet the serial is in | Hopper Type | KB to use |
|---|---|---|
| `RC28 Classified` | VARIABLE | VHRS28 |
| `RC28 Classified` | FIXED | FHRC28 |
| `RC36 Classified` | VARIABLE | VHRS36 |
| `RC36 Classified` | FIXED | FHRC36 |

What the workbook contains:

- **Classified sheets:**
  - `RC36 Classified`: 493 serials, 331 variable and 162 fixed. Columns: Parent Part Number, Parent Description, Hopper Type, Classification Basis.
  - `RC28 Classified`: 457 serials, 413 variable and 44 fixed. Columns: Parent Part Number, Parent Description, Child Description, Hopper Type, Classification Basis.
  - The column positions differ between the two sheets, so read columns by header name, not by index.
- **No overlaps:** no serial appears in both classified sheets.
- **Raw BOM sheets** (`RC36`, `RC28`): these are for reference only. Do not route from them.
- **Classification Basis:** this shows how certain each row is. About 145 RC36 rows say "Inferred from child part descriptions…", which means they were not classified directly from the parent description. For the smoke test, **only pick serials whose basis comes from the parent description** (dual-length X/Y', "FIXED"/"VARIABLE" in the name, or the "V"/"S" designation).
- **Default serial:** `K7170` is in `RC28 Classified` as VARIABLE, so it routes to **VHRS28**. Its BOM briefly listed an RC36 computer (added 2017-05-15, deleted 2017-06-07), and the current computer is RC28. Route by the classified sheet only.

Write `lkqa/routing.py` with `kb_for_serial(serial) -> (model, kb_file)`. It must raise a clear error if the serial is unknown. Unit-test it with:

- K7170 → VHRS28
- one serial for each of the other three models, taken from the workbook
- an unknown serial

The selected serial, its model, the KB file and the classification basis all go into the report header.

### Question bank: `kb/question_bank.yaml`

1. Build the bank from these KBs. Each entry contains:
   - `id`, `model`, `kb_file`, `kb_section` (the exact heading)
   - `question`: phrased the way a field operator would ask it on a call
   - `steps`: ordered list. Each step has the KB text plus `keywords`: the required terms, each with a list of acceptable synonyms.
   - `cautions`: each caution has its KB text, `keywords`, and `step` (the step number it belongs to, or `procedure` if it covers the whole procedure).
2. Only include procedures that have **≥3 steps AND at least one caution/warning**. Good candidates (verify each one against the files):
   - Startup sequences
   - "After hydrostatic system work" startup
   - Material calibration
   - Gate transducer calibration
   - Engine-won't-crank troubleshooting
3. Generate entries with a script, `tools/build_question_bank.py`, that parses the KBs. Then hand-review the keywords. Do not invent any step or caution that is not in the KB text. Commit the reviewed YAML.
4. Selection:
   - Each run picks one entry **for the model the call is dispatched for**. A question from a different model's KB is never valid.
   - Log the seed so the run can be reproduced.
   - `KB_QUESTION_ID=` pins a specific entry.

## The flow every LiveKit test follows (fixed; only the KB question varies)

1. **Call starts.** Join the room; the agent is dispatched. Assert the agent joins within the timeout.
2. **Agent greets.** Assert a greeting arrives. Handle serial and read-back exactly as the current test does.
3. **Test agent asks the KB question** chosen from the bank.
4. **Agent responds.**
   - It may ask follow-up or clarifying questions. Answer them so the call keeps moving.
   - If it gives a summary, a partial answer, or one step at a time, the test agent **explicitly asks for the complete step-by-step procedure, including any cautions**. Keep collecting until the full answer is in or the turn limit is reached.
   - Ignore "let me check" holding turns.
5. **Validate** the combined answer, meaning every agent answer turn after the question, using the rules below.
6. **Test agent says thank you.** Send this after validation. If validation failed, record the failure and still finish the call so the report has the full transcript.
7. **Agent asks for feedback.** Assert that the agent asks for a rating.
8. **Test agent answers with a random integer from 1 to 10.** Log the number.
9. **Call closes.** Assert the call ends within the timeout. Never leave a room open; hang up in `finally`.

Each stage is a named, timed checkpoint with its own pass/fail in the report:
`call_started, greeted, question_asked, answer_received, answer_valid, thanks_sent, feedback_asked, feedback_answered, call_closed`.

## Validation rules: keyword matching, deterministic, no LLM judge

The answer passes only when **every step and every caution passes**. Any single failure fails the test.

**Rewording within a sentence is a pass.** A step passes when all of its required keywords (or a listed synonym for each) appear in the agent's text for that step, regardless of sentence structure or filler words. Normalize before matching:

- case and punctuation
- curly quotes
- spoken numbers: "forty to sixty" = "40–60" = "40 to 60"; "thirty seconds" = "30 seconds"
- units: "PSI" / "P S I"; "FPM" / "feet per minute"
- simple plurals

**Comparing step to step fails on any of these:**

1. **Missing step**: a KB step whose keywords are not found anywhere in the answer.
2. **Out of order**: the steps are found, but not in the KB order.
3. **Merged or skipped**: two KB steps are both matched inside one agent step, or the agent collapses several steps into one summary line.
4. **Missing caution**: a KB caution's keywords are not found.
5. **Misplaced caution**: a caution tied to a specific step does not appear within that step or immediately next to it. A `procedure`-level caution can appear anywhere in the answer.
6. **Contradicted value**: a number, position or setting that differs from the KB (e.g. "crank for 60 seconds" when the KB says 30, or IDLE instead of RUN). Check this for every numeric or position keyword in the entry.

Splitting the answer into steps: use the agent's numbering or ordinals ("first", "step two", "next", "then", "after that", "finally"). If there are no step markers, use sentence boundaries. Record the split in the report so a failure can be checked by eye.

Unit-test the validator offline, with no live call:

- one fixture of passing transcripts per failure rule
- one fixture of failing transcripts per failure rule
- a reworded-but-correct transcript that must pass

## CI pipeline (YAML): runs on every push to this branch and on demand

1. **Clean slate.** No cache restore. Delete old Playwright browsers, the pnpm store, the uv cache and any previous `report/` contents.
2. **Install fresh.** `uv sync`, `pnpm install`, then `playwright install --with-deps chromium`. The browser is downloaded on every run.
3. **Validator unit tests.**
4. **UI test** (Playwright, browser).
5. **LiveKit KB-steps call test** (this flow).
6. **Build the HTML report.** Always runs, even when earlier steps failed (`if: always()`).
7. **Publish on every run**, pass or fail, and put the report link in the job summary.
8. Secrets come from CI secrets and are never echoed.

## HTML report: the primary deliverable, written for non-technical readers

- `report/index.html` is the **primary** report and is what opens by default when the run's report link is clicked.
- Top of the page: a large PASS/FAIL banner, run time (IST), branch, commit, duration, and the model and KB file used.
- The 9 checkpoints in plain English, each with pass/fail and its timing.
- The question and its KB section. Then a step-by-step table with these columns:
  - **KB step / caution**
  - **What the agent said** (the matched segment)
  - **Keywords found / missing**
  - **Result**: Pass, Missing, Out of order, Merged, Misplaced caution, or Wrong value

  Every failure gets a one-line plain-English reason.
- The full call transcript in chat-bubble style with timestamps, including the random feedback number.
- "Technical details → Playwright report" link (`report/playwright/index.html`), plus the trace and screenshots on failure.
- Self-contained (inline CSS/JS), readable on a phone, with no jargon in the top section.

## Open questions: ask me these before writing any code

1. **Serial and model per run:** routing already resolves K7170 to VHRS28. Should every smoke run stay on K7170/VHRS28, or pick a random serial (and so a random model) from the workbook each time? Does the deployed agent choose its KB from the serial alone, or does `KNOWLEDGE_BASE_ID` / product metadata also have to change per model? If it does, what are the IDs for VHRS36, FHRC28 and FHRC36?
2. **Call channel:** should the KB call stay on the LiveKit SDK as text on `lk.chat` (the current approach), or must it go through the browser UI with voice? Does the Playwright UI test still run before it, as in `make test`?
3. **Thank-you and feedback wording:** is there a fixed thank-you phrase, or will any natural thanks do? What exact phrases does the agent use to ask for feedback? Should a missing feedback question fail the test or only warn?
4. **Call closure:** who ends the call, the agent after the rating or the test agent? What is the maximum wait before it counts as a failure?
5. **CI platform:** GitHub Actions? Which runner: ubuntu-latest or self-hosted? Which triggers: push to `develop-phase1_basic`, manual dispatch, a schedule (at what time IST)?
6. **Publishing:** GitHub Pages, artifact only, or both? Keep a history of runs or only the latest? Who needs access, and is the repo private?
7. **Environment:** should the smoke run target `etnyre-dev.thinknetic.app` with agent `thinknetic-agents-nonprod`, or something else?
8. **Retries:** should a failed live call retry once in CI, or fail immediately?

## Done means

- `make smoke` runs the whole sequence locally, in the same steps as CI.
- The validator and routing unit tests pass.
- One CI run on the branch shows a published `index.html` with:
  - all 9 checkpoints
  - the step-by-step KB comparison table
  - the transcript
  - a working link to the Playwright report
- The README explains how to add a KB question and how to read the report.
