# Architecture

## Principle

Test the deployment, not the code. Nothing in this repo imports, builds, mocks or
instruments the application. Every layer talks to `BASE_URL` over the network
exactly as a user or a client would, which means the same suite points at dev,
staging or prod by changing one environment variable.

## Layers

```
          +-------------------------------+
          |  ui/     Playwright + TS      |  what a user can see and do
          +-------------------------------+
          |  api/    pytest + httpx       |  what the client is served
          +-------------------------------+
          |  voice/  LiveKit Python SDK   |  what the agent actually says
          +-------------------------------+   (phase 3)
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
pipeline later, porting `api/` to Rest Assured is a contained job; nothing else
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
borderline score never blocks a release on its own. The `judge` seam is not built
yet; `voice/` and the chat placeholder are where it will attach.

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
3. **Phase 3** - `voice/` against LiveKit directly: connection integrity,
   turn-taking via VAD, local transcription for content checks, barge-in.
4. **Later** - semantic scoring layer, concurrent-call load with k6 or Locust,
   Allure for a single cross-layer report.
