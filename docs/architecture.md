# Architecture

## Principle

Test the deployment, not the code. Nothing in this repo imports, builds, mocks or
instruments the application. Every layer talks to `BASE_URL` over the network
exactly as a user or a client would, which means the same suite points at dev,
staging or prod by changing one environment variable.

## Layers

```
          +-------------------------------+
          |  tests/ui/     Playwright + TS      |  what a user can see and do
          +-------------------------------+
          |  tests/api/    pytest + httpx       |  what the client is served
          +-------------------------------+
          |  tests/sdk/    LiveKit Python SDK   |  what the agent actually says
          +-------------------------------+   (phase 3)
          |  tests/judge/  LLM-as-judge + SDK   |  whether what it says is in
          +-------------------------------+   the manual
```

Cheapest signal first. The API suite runs before the UI suite in CI because a
broken payload makes every browser assertion downstream meaningless - and it
takes seconds rather than minutes to find out.

## Why two languages

Not a preference, a constraint. Playwright's TypeScript API has the best
auto-waiting and the trace viewer, which matters for a React SPA whose agent
widget appears asynchronously. LiveKit's usable client SDKs for a test harness
are Python and JS, and the Python audio ecosystem (`webrtcvad`, `faster-whisper`,
`soundfile`) has no real equivalent in Node. The `Makefile` and a shared
repo-root `.env` keep the seam from leaking into daily use.

Java/Rest Assured was considered to match the existing team tooling. It loses on
the voice path - there is no maintained LiveKit Java client - so it would need a
Python sidecar anyway. If the API suite needs to land in the existing Jenkins
pipeline later, porting `tests/api/` to Rest Assured is a contained job; nothing else
depends on its language.

## Determinism

The current assertion set is entirely deterministic: status codes, element
presence and absence, socket establishment, latency budgets. This is a deliberate
choice for phase 1 - a suite that is green for the right reasons is worth more
than broad coverage nobody trusts.

LLM output is not deterministic, so asserting on reply wording produces a suite
that is red every morning for no reason. When semantic coverage is added, it
should be threshold-based scoring (faithfulness to the KB, refusal correctness,
escalation triggering) reported separately from the pass/fail suite, so a
borderline score never blocks a release on its own.

That seam is now `tests/judge/`, and it holds to every part of the above. It scores
seven rubrics 0.0-1.0 against the knowledge-base section a question came from -
never against the judge model's own knowledge, which contains no Etnyre manual
and would grade on plausibility instead. It reports to
`report/data/judge-scores.json` and gates nothing: `judge.requireScoreGate` and
`judge.requireSafetyGate` both ship off, because the thresholds were read off
the manuals rather than measured from calls, and a gate on a guessed threshold
is the same mistake this document records about the latency budgets below.

Its offline half - rubric validation, KB grounding, anchor parity with the
browser suite - needs no network and no API account, and is cheap enough to run
on every PR. That half is what stops the expensive half scoring confident
nonsense.

There is now a third thing in `tests/judge/`, and it is neither of the above:
`oracle.py` is a DETERMINISTIC assertion layer. Where the scorer asks a model
whether an answer is faithful, the oracle asks questions that have crisp
answers - did the agent state a number that appears in no manual we hold, did
it quote a figure belonging to a different machine, did the safety line come
before the first step - and answers them by parsing, against an index compiled
from the knowledge bases at `make resources` time. Same transcript in, same
verdict out, offline, forever.

That is the distinction this section was reaching for. Asserting on WORDING is
what produces a suite that is red every morning; asserting on the NUMBERS a
manual commits to does not, because paraphrase does not move a number. So the
oracle can eventually gate where a score cannot - and it still ships with every
gate off, because the gate is a statistic over k runs and there is no baseline
yet. See deterministic-kb-testing.md.

## Latency budgets

`agent-entry.spec.ts` asserts time-to-connected under 15s. That number is a
placeholder, not a measurement. Collect a week of real values from the dev
environment and set the budget at roughly p95 - a budget invented before you have
baseline data either never fires or fires constantly.

## Environment safety

The dev deployment is shared. Workers are capped at 3 locally and 2 in CI, and
the tests that open a real agent session are tagged `@live` and run serially, so
the suite does not turn into an accidental load test. Run
`--grep-invert @live` when you only need the static checks.

## Roadmap

1. **Now** - page functional + public API, deterministic.
2. **Next** - chat mode once it is enabled on dev; authenticated flows using the
   better-auth login (note the cookie naming/URL-encoding quirk when you get there).
3. **Now, gating offline** - `tests/judge/src/oracle.py`: deterministic KB assertions
   (ORC-01..12 on every PR, `make oracle` over recorded calls). Report-only on
   real calls until a fortnight of nightly runs re-bases the gates.
4. **Phase 3 (built 2026-09-28)** - `tests/sdk/` against LiveKit directly (docs/livekit-sdk-testing.md): connection integrity,
   turn-taking via VAD, local transcription for content checks, barge-in.
   Sessions come from the product's public session endpoint (the token carries
   the dispatch to `thinknetic-agents-nonprod`); text, audio publishing, local
   transcription and barge-in are all built.
5. **Now, reporting only** - `tests/judge/`: semantic scoring against the KB. Turn
   `requireSafetyGate` on once a fortnight of scores has re-based the thresholds.
6. **Later** - concurrent-call load with k6 or Locust, Allure for a single
   cross-layer report.
