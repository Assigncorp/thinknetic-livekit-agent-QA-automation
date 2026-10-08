# Thinknetic LiveKit agent: smoke test

This is the standard smoke test for the deployed Etnyre ChipSpreader support agent. Every run executes two stages in order:

1. **Unit checks** (offline):
   - serial-to-model routing
   - the step-by-step answer validator
   - the question bank, checked against the knowledge bases
2. **LiveKit KB-steps call** ([test_kb_call.py](tests/sdk/tests/test_kb_call.py)). One live call to the deployed agent over the LiveKit SDK asks a real question from the machine's knowledge base. The answer is checked step by step and caution by caution against the KB text. The caller then asks for the same steps by text, and the text the agent sent is read from the agent's own logs and checked the same way.

A failure in stage 1 stops the run before the live call. The HTML report is built every time, pass or fail.

The product-page UI test (Playwright) is no longer here. It now lives in its own repo.

## Run it

```bash
brew install livekit-cli # the `lk` CLI, to read the agent's logs (CI installs it too)
cp .env.example .env     # fill in LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
make smoke               # clean, install, unit, kb, report - the same steps as CI
open report/index.html
```

| Command | What it does |
|---|---|
| `make test` | The same sequence without the clean and install steps. |
| `make unit` | Unit checks only. Results go to the internal report, `report-internal/index.html`. |
| `make kb` | Live call only. |
| `make report` | Builds `report/index.html` from whatever has run. |
| `KB_SEED=123456789 make kb` | Repeats a run's exact model and question. The seed is printed and shown in the report. |
| `KB_MODEL=FHRC28 make kb` | Pins the model. |
| `KB_QUESTION_ID=<id> make kb` | Pins one question. |

The live test skips if the LiveKit credentials are missing.

## The live call

Each run picks one of the four machine models at random. It uses that model's smoke serial and asks one question from that model's own KB; a question from another model's KB is never asked. Every call follows the same eleven steps, and each one is a timed checkpoint in the report:

| # | Checkpoint | What happens |
|---|---|---|
| 1 | `call_started` | The test joins a fresh room and the agent is dispatched into it. The agent must join within 15 s. |
| 2 | `greeted` | The agent greets the caller. Serial look-up, read-back and the agent's "last time…" recap are all handled. |
| 3 | `question_asked` | The test caller asks the KB question. |
| 4 | `answer_received` | The agent answers. It gives one step per turn, so the caller declines the offer to text the steps, asks for the complete procedure including cautions, and says "done, what's next?" after each step. Collecting stops when every KB step and caution has been said, or at the turn limit. "Let me check" holding turns are ignored. |
| 5 | `answer_valid` | The combined answer is validated (rules below). |
| 6 | `text_asked` | The caller asks for the same steps by text, gives the test phone number when asked, and confirms the read-back. The agent must answer the request. |
| 7 | `thanks_sent` | The caller says thank you. This happens even if validation failed, so the report has the whole call. |
| 8 | `feedback_asked` | The agent must ask for a rating. |
| 9 | `feedback_answered` | The caller answers with a random integer from 1 to 10, which is logged. |
| 10 | `call_closed` | The agent must end the call within 30 s. The test always hangs up at the end, so no room is left open. |
| 11 | `text_valid` | After the call, the agent's worker logs for the room are read with `lk agent logs`. The text the agent sent (`sending_text … message='…'`) is checked against the KB like the spoken answer. |

A failed call is retried once in a fresh room. The report shows that a retry happened and includes both transcripts.

**How the answer is validated.** The check is deterministic keyword matching, with no LLM judge ([validator.py](tests/sdk/lkqa/validator.py)).
- **What passes.** A step passes when all its keywords (or a listed synonym) appear in the agent's text for that step. Rewording is fine.
- **The pass mark.** The call passes when at least 95% of the KB's steps and cautions match (`KB_PASS_THRESHOLD`), and none of the misses is a wrong value. This applies to the spoken answer and to the texted steps. With 4 to 17 items per question, 95% still means every item for all 26 current questions; one miss only becomes possible at 20 or more items, or by lowering the threshold.
- **Normalisation.** Both sides are normalised first: case, punctuation, curly quotes, spoken numbers ("forty to sixty" = "40–60"), units ("P S I" = PSI, "feet per minute" = FPM) and plurals.
- **Splitting.** The answer is split into steps using the agent's own markers ("step two", "next", "finally", "1.") and its turns. With no markers, it is split by sentences.
- **What fails.** A wrong value always fails the call. Any of these fails it when the share of matched items falls below the pass mark:
  - a missing step
  - steps out of order
  - two steps merged into one
  - a missing caution
  - a caution not given with its step
  - a wrong value (a number or position that contradicts the KB, such as "60 seconds" for 30, or IDLE for RUN)

**Which KB a serial uses.** `kb/hopper_classification.xlsx` decides this. Only the two classified sheets are used, never the raw BOM sheets:

| Sheet | Hopper type | KB |
|---|---|---|
| RC28 Classified | VARIABLE | VHRS28 |
| RC28 Classified | FIXED | FHRC28 |
| RC36 Classified | VARIABLE | VHRS36 |
| RC36 Classified | FIXED | FHRC36 |

The four smoke serials are listed in `kb/smoke_serials.yaml`: K7170, K7174, K6757 and K6758. Every run first checks that each one still routes to its listed model, classified directly from its parent description, and fails the run if not.

## Add a KB question

1. **Find the procedure in the model's KB.** It qualifies only if it has **at least 3 ordered steps and at least 1 caution or warning** (`> **WARNING:**`, `**Caution:**`, a nested `> **CAUTION:**`, or "Do NOT …" inside a step).
2. **Generate the draft.** Run `make bank-draft`. It prints every qualifying procedure, with the reason each other one was dropped, and writes `kb/question_bank.draft.yaml`. The step and caution text in the draft is verbatim from the KB.
3. **Copy the entry into `kb/question_bank.yaml`.** Then:
   - Write `question` the way an operator would ask it on a call. Don't give away any step or value.
   - Give every step 1–4 `keywords`: the distinctive component plus the action, position or value. Each keyword's `term` must appear in that step's KB text. Add realistic spoken `synonyms`. Mark numbers with units as `kind: value`, and PARK/RUN/ON/OPEN-style settings as `kind: position`.
   - Anchor each caution to its step number, or to `procedure` if it covers the whole procedure, and give it 1–3 keywords.
4. **Check the bank.** Run `make check-bank`. It fails if:
   - any text is not verbatim from the KB
   - a keyword is missing from its own step
   - two steps' keywords overlap so much that a correct answer would read as "merged"
   - the KB's own text would not pass the validator
5. **Try it live.** Run `KB_QUESTION_ID=<your id> make kb`.

## Read the report

`report/index.html` opens in any browser and works on a phone.

- **Banner.** PASS or FAIL for the whole run, with:
  - run time (IST), duration, branch and commit
  - the machine model, serial and KB file used, and why that serial is that model
  - on failure, **Reference for what failed**: the LiveKit room ID (`RM_…`) and room name of every failed call. Search for these in LiveKit Cloud or the agent logs.
- **What was checked.** The phone-call check. The unit checks are not in this report.
- **The phone-call check.**
  - The question and the KB section it came from.
  - For each attempt: **Call reference** (LiveKit room ID, room name, start time, agent participant), then **Question asked** (exactly as said on the call) and **Answer received** (the agent's answer turns, in order).
  - The eleven checkpoints in plain English, each with its result and timing.
  - **The answer, step by step.** For every KB step and caution: what the agent said, the keywords found and missing, and the result (Pass, Missing, Out of order, Merged, Misplaced caution or Wrong value). Every failure has a one-line reason, and "How the answer was split into steps" shows the split so you can check it by eye.
  - **The call, as it happened.** The full transcript as chat bubbles with timestamps, including the random rating.
- **Technical details.** A link to the raw call data and the exact command to re-run the same call.

## CI

[.github/workflows/smoke.yml](.github/workflows/smoke.yml) runs on every push to `develop-phase1_basic` and on demand from the Actions tab. A manual run can set the seed, model or question.

- It starts from a clean slate: no restored caches and old reports removed. It then runs the same steps as `make smoke`.
- The report is built and published on every run, pass or fail:
  - **GitHub Pages** holds the latest run; the link is in the run summary.
  - **The `smoke-report-<n>` artifact** keeps every run.
- The unit checks are not in that report. They go to `report-internal/index.html`, kept as the separate `internal-unit-checks-<n>` artifact and never published to Pages.
- One-time setup:
  - Repository secrets `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.
  - Settings → Pages → Source = **GitHub Actions**.

## Layout

```
kb/                                 the four model KBs (unchanged), hopper_classification.xlsx,
                                    smoke_serials.yaml, question_bank.yaml (reviewed)
tests/sdk/lkqa/routing.py           serial -> model -> KB
tests/sdk/lkqa/bank.py              picks model, serial and question (seeded)
tests/sdk/lkqa/kbcall.py            the eleven-checkpoint live call
tests/sdk/lkqa/validator.py         deterministic step/caution validator
tests/sdk/lkqa/expect.py            LiveKit-style expect() assertions over the recorded call
tests/sdk/lkqa/call.py              LiveKit room, agent dispatch token, turn reading
tests/sdk/tests/                    test_kb_call.py (live), test_routing / test_validator /
                                    test_question_bank (offline), fixtures/validator/
tools/build_question_bank.py        KB -> question bank draft
tools/check_question_bank.py        question bank checker
tools/build_report.py               report/index.html
```
