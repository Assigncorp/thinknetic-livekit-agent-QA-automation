# `tests/judge/` — semantic scoring, and a LiveKit caller to feed it

The layer `docs/architecture.md` leaves a hole for:

> LLM output is not deterministic, so asserting on reply wording produces a
> suite that is red every morning for no reason. When semantic coverage is
> added, it should be threshold-based scoring (faithfulness to the KB, refusal
> correctness, escalation triggering) reported separately from the pass/fail
> suite, so a borderline score never blocks a release on its own. The `judge`
> seam is not built yet.

This is that seam, plus the LiveKit-SDK caller that produces the transcripts it
scores.

```
make judge-offline   # rubrics + KB grounding. No network, no account. Gates a PR.
make judge           # score recorded calls.   Needs ANTHROPIC_API_KEY.
make judge-report    # show the last report/data/judge-scores.json
```

---

## The one idea this rests on

**The knowledge base is the arbiter, not the model.**

The obvious way to build this is to ask a model "is this a correct answer about
an Etnyre chip spreader?". That does not work, and it fails in a way that looks
like it is working. No model's training data contains the Etnyre manual, so it
grades on plausibility: a fluent wrong answer scores well and a correct terse
one scores badly, and the whole suite quietly becomes a test of whichever model
is judging.

So the judge is never asked whether an answer is right. It is handed the KB
section the question came from and asked whether every claim is supported *by
that text*. It is told in as many words that its own knowledge of this equipment
is not evidence. That turns a question models are bad at into one they are good
at, and it makes the manual — not the judge — the thing that decides.

Everything else here follows from that, including the parts that look fussy:

- **The section, not the file.** `src/corpus.py` hands over the `##` section's
  preamble plus the one `### Q:` entry the question came from — about 1.8k
  characters, against 474 lines for the whole of vhrs28.md Section 8. Given the
  entire KB, an answer describing the RC-36 gate procedure to an RC-28 caller
  reads as "supported by the manual", because *some* section supports it. That
  is exactly the cross-family defect the suite exists to catch.
- **The preamble comes too.** These sections write their safety warning once, at
  the top, and thirty entries inherit it. Grading an answer that carries that
  warning against a slice that does not contain it marks the agent down for
  being careful.
- **Every score carries evidence.** Each rubric returns a verbatim quote from
  the transcript and from the manual. A judge that returns `0.4` and a paragraph
  of reasoning cannot be audited; one that returns `0.4` and the sentence it
  objected to can be argued with — which is the only way the thresholds ever
  stop being guesses.

## The whole answer is the unit

From `docs/chat-flow.md`: this agent is a guided walkthrough, not a Q&A bot.
Asked a question straight out of the manual it opens with a safety preamble,
offers to text the steps, and then delivers the procedure **one step per turn**.
The manual's facts — `1000 PSI`, `P2-PIN 19`, `240 ohms` — are several turns in.

Scoring "the reply" therefore scores an acknowledgement. `Transcript.full_answer`
accumulates every agent turn after the question landed, and that is what gets
judged. A call whose accumulated answer is under `judge.minScoredTurnChars` is
recorded as **not scored**, with a reason, rather than scored zero — a zero there
describes the harness, not the agent.

## What it will not mark you down for

Written into the judge's system prompt, because each one is correct behaviour
for this deployment and each one looks like a defect to a naive grader:

- speaking numbers as words (`"four hundred feet per minute"` *is* `400 FPM`)
- a procedure spread across several turns
- a safety warning before the steps
- a diagnostic question before the answer
- offering to text the steps
- being terse, if it is correct

`test_judge_agreement.py::test_a_faithful_answer_scores_well` exists to catch a
judge that forgets this. It is the easiest failure to miss, because a judge
scoring good calls badly still produces a full report of plausible numbers.

---

## Layout

| File | What it does |
|---|---|
| `src/corpus.py` | Slices the KB down to the section a question came from. The part that decides whether a score means anything. |
| `src/scorer.py` | Builds the prompt and calls the judge. `build_prompt()` is pure, so the offline suite asserts on what the judge is actually shown. |
| `src/anchors.py` | Port of `tests/ui/src/utils/anchors.ts`. Matches a KB fact written or spoken. |
| `src/transcript.py` | `Turn` / `Transcript`, and `full_answer`. |
| `src/livekit_probe.py` | `make probe-agent`: which agent worker joins this deployment. |
| `src/report.py` | `report/data/judge-scores.json`. |
| `tests/test_rubric_catalog.py` | 42 offline checks. Gates a PR. |
| `tests/test_judge_agreement.py` | Is the instrument working? Run this after changing the model, a rubric, or the grounding window. |
| `tests/test_recorded_calls.py` | Score the recordings. Report-only. |

Everything configurable is in the `judge` block of `config/testbed.config.json`.
No machine names, tyre pressures or phone numbers are hardcoded anywhere in this
package — renaming a KB or adding a machine is a config edit, as everywhere else
in this repo.

### Why `anchors.py` is a duplicate

Because the browser suite and this one must agree on whether an answer cited
`400 FPM`. When they disagree the report says the agent both did and did not
cite the manual, and nobody can tell which half is wrong. Two implementations of
eighty lines of regex, tested against the same cases, beat a cross-language
bridge. **If you change one, change both** —
`test_an_anchor_does_not_match_inside_a_longer_number` is there because they
already drifted once.

---

## What runs today (updated 2026-09-28)

**The LiveKit half runs.** `judge.livekit.agentName` was a placeholder
(`"etnyre-support"`) and `make probe-agent` proved no worker owns it. The real
name, `thinknetic-agents-nonprod`, was read off a live session - it is the
`agentName` in the `roomConfig.agents` dispatch inside the token the product
page is issued. More importantly, the page never dispatches anything itself: it
POSTs the intake form to the public `assistant-session` endpoint and joins with
the token that comes back.

Calls are driven by `tests/sdk/` - contract, auth, KB grounding over every machine,
traps, voice, concurrency - which scores with this package's `src/oracle.py`
and writes every call to `report/data/recordings/`. The judge's own caller
(`src/livekit_call.py`, `make judge-live`) was removed on 2026-09-28: `tests/sdk/`
does the same job correctly, and two copies of the turn-taking loop is one
too many. See docs/livekit-sdk-testing.md.

**The LLM judge still needs a credential.** Set `ANTHROPIC_API_KEY` in `.env`,
or `ant auth login`. `make judge-offline` and the deterministic oracle need
neither. To LLM-score live calls, point the judge at the SDK's recordings.

### The recordings are synthetic

`tests/judge/recordings/` currently holds two hand-written transcripts, clearly
labelled `_synthetic`, one deliberately good and one with three planted defects.
They exist to exercise the harness and to act as the judge's own regression
cases. **They are not measurements of the agent** and no score derived from them
says anything about the deployment. Real captures now land in
`report/data/recordings/` from both `tests/sdk/` and the browser chat suite; score them
with `make oracle DIR=report/data/recordings`.

---

## Gating

Off. Both switches.

```jsonc
"requireScoreGate":  false,   // any rubric under threshold fails the run
"requireSafetyGate": false,   // only noFabrication + controllerFamily fail
```

The thresholds in config were set by reading the manuals, not by scoring calls.
A gate on a guessed threshold either never fires or fires constantly, and
`docs/architecture.md` already records that lesson about the latency budgets.
Collect a fortnight of `report/data/judge-scores.json`, re-base the thresholds from
the distribution, then turn `requireSafetyGate` on first — a fabricated
specification and a cross-family procedure are the two failures that actually
reach a machine.

`test_gating_is_off_until_there_are_baselines` fails if you flip one without
deleting it, so turning a gate on is a deliberate act with a commit message
attached.

## Cost

One request per call scored. The rubric definitions are a stable prefix with a
cache breakpoint on them; the KB extract and the transcript vary per call and sit
after it. The judge model is `judge.model` — `claude-opus-5` by default, because
a judge must be at least as capable as the thing it is judging or it marks good
answers down for reasoning it cannot follow. Drop it to `claude-sonnet-5` once
`test_judge_agreement.py` still passes on it; that is what those cases are for.
