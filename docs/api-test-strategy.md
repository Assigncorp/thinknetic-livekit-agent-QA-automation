# API test strategy: rate limiting and performance

Scope: the public HTTP surface at `BASE_URL` — the product endpoint the SPA
hydrates from, its fail-closed variants, and `/env.js`. Black-box, no
application code. Everything here lives in `tests/api/` and runs without a browser.

This document covers two areas the phase-1 suite did not: whether the rate
limiter behaves the way clients are told it does, and whether the endpoint is
fast enough to use in the field. Risk #5 on [test-plan.md](test-plan.md) —
"latency makes the agent unusable in the field" — was previously covered by a
single request timed against 3 seconds.

---

## 1. What the environment actually does

Everything below was measured against `etnyre-dev.thinknetic.app` on
2026-09-21. It is written down because every decision in this strategy follows
from it, and because when one of these facts changes the strategy should
change with it. Each one has a test that fails when it stops being true.

### The rate limiter

Every `/api/v1` response carries:

```
x-ratelimit-limit: 100
x-ratelimit-remaining: 99
x-ratelimit-reset: 60
```

| Property | Finding | Consequence |
|---|---|---|
| Limit | 100 requests | Per **serverless instance** — see below |
| Window | 60s, fixed | `reset` counts **down** in seconds; it is not a unix timestamp |
| Scope | One bucket across the whole API prefix | Product, unknown-product and unknown-org paths all draw on the same counter |
| Failures | **404s are charged** | The fail-closed tests spend quota they never declared |
| Conditional GETs | **304s are charged** | ETag caching saves bandwidth, not quota |
| `/env.js` | **No limiter headers at all** | Served as a static asset, outside the bucket, free to measure |

The existing functional suite already spends roughly 15 requests per run
without accounting for any of them.

### The counter is per instance, not per client

This is the most important finding in this document and it was nearly missed.

With a single instance warm, 25 consecutive requests decrement cleanly from 99
to 75. With several warm — which the concurrency probe in PERF-08 causes all by
itself — independent counters interleave, each with its own count and its own
window phase:

```
stream A:  65 64 63 62 61 60 59 58 57 56 55 54 53 52 51    reset 23 -> 13
stream B:  89       77 76             75       74          reset  8 ->  6
```

Two consequences. The **effective ceiling is 100 × (warm instances)**, not 100 —
so the suite's pacing is conservative rather than wrong, which is the safe
direction to be wrong in.

The one that matters is that **`x-ratelimit-remaining` is not something a client
can act on.** Its entire purpose is to let a caller back off before being
throttled, and a caller reading `51` may see `74` on its next request and `8`
on the one after. It cannot tell "plenty left" from "one request from a 429 on
whichever instance answers next". That is a real weakness in a public contract,
and it is worth a decision rather than an incident. RL-11 measures it every run
and reports it; it fails only when `rateLimit.requireGlobalConsistency` is
turned on, which is off because this is a property of the platform's scaling
rather than of this deployment's code.

It also had a direct effect on the tests. RL-04, RL-05 and RL-06 originally
compared two consecutive readings and treated a count that went *up* as a
window rollover, skipping themselves. It is not a rollover — it is a different
instance answering — so those tests were silently skipping **exactly when the
deployment was busiest**, which is when they are most worth running. They now
retry until both readings come from one instance (`instanceHopRetries`, 6) and
fail informatively if they cannot, instead of skipping. Verified by running the
rate-limit suite immediately after the perf suite, with two limiter states
live: all three pass where they previously skipped.

### Latency and payload

A 20-sample run from one client:

| Measurement | Observed | Budget now set |
|---|---|---|
| Warm p50 | 422 ms | 900 ms |
| Warm p95 | 500 ms | 1500 ms |
| Warm max | 540 ms | 3000 ms |
| Spread (p95/p50) | 1.18 | 4.0 |
| First request, cold deployment | 2090 ms | 4000 ms |
| First request, warm deployment | 693–783 ms | — |
| 404 path p95 | 426–551 ms | 1500 ms |
| `/env.js` p95 | 60 ms | 800 ms |
| Payload | 22 710 B raw → 5 669 B brotli (4.0×) | 65 536 B, min 2.0× |

Two things stand out. The endpoint is **very consistent when warm** — a spread
of 1.18 over 20 samples is tight, which is what makes a tail budget meaningful
here at all. And the error path costs the same as the happy path, which is the
right answer: a cheap 404 is what stops slug enumeration being an amplification
attack.

Budgets sit at roughly 2–4× the observed figure. That is loose on purpose. This
runs against a shared dev deployment with other people on it, and **a perf gate
that flaps gets muted within a fortnight**. They are placeholders in the same
sense as the agent budgets in `testbed.config.json`: re-base them from
`report/data/api-perf.json` once a week of runs has accumulated.

---

## 2. Why this is sampling, not load testing

The obvious question is why there is no k6, Locust or Artillery here.

**Because the endpoint permits 100 requests per minute and counts every
failure.** A load tool's entire value is generating sustained concurrent
traffic and reporting what breaks. Against this limiter, every run past the
first few seconds would be measuring the limiter's own 429 path. The result
would not be a latency profile of the API; it would be a very expensive
latency profile of a rate limiter, produced by a second toolchain, a second
CI job and a second reporting format that nobody reads.

So the approach is **statistical sampling within the quota**: 20 warm samples
for a distribution, 10 parallel ones to prove the endpoint does not serialise,
and small sets for the error and config paths. Roughly 46 requests per run,
inside one window, in about 15 seconds.

Reach for a real load tool when — and only when — one of these becomes true:

- the limit is raised, or the suite gets an allow-listed egress IP;
- a dedicated performance environment exists that nobody else is using;
- the question changes from *"is this fast?"* to *"how many concurrent callers
  before it degrades?"* — which is a capacity question this suite cannot and
  should not answer.

Until then, k6 would be a second toolchain producing worse data than 60 lines
of `httpx`.

---

## 3. The quota problem, and how the suite solves it

Adding performance tests to a suite that shares a 100-request window with the
browser suite, CI and anyone clicking through the dev site creates a failure
mode worse than the gap it closes: **a perf test exhausts the window, and the
functional tests behind it fail on 429s that have nothing to do with what they
were checking.** Someone then spends an afternoon debugging a product that is
working perfectly.

Three mechanisms prevent that.

**A session-wide bucket.** `tests/api/src/utils/ratelimit.py` defines `Bucket`,
registered as an `httpx` response event hook on every client in `conftest.py`.
Every response the suite receives — functional, perf, 404, anything — updates
one shared view of the window. Nothing has to remember to report its spending.

**A reserve floor.** `rateLimit.reserveFloor` (15) is quota the suite will not
spend. Before a measurement, `bucket.reserve(n)` checks whether taking `n` more
requests would dig below it; if so it parks until the window rolls over and
prints why:

```
[rate limit] 99/100 left, window resets in 60s; 1 more requested
             for payload size - waiting 61s for the window to roll over
```

The floor exists because this suite is not the only caller. Spending the last
of a window so a percentile could have one more sample is a self-inflicted
outage for a colleague.

**Lazy priming.** The first reservation in a session has nothing to reserve
against — no response has been seen, so the throttle cannot tell a fresh window
from the tail of an exhausted one. `Bucket.set_primer` spends exactly one
request to find out, and only when something actually reserves. The catalogue
suite, which makes no network calls at all, stays offline.

**Serial execution.** `tests/api/pyproject.toml` deliberately does not enable
`xdist`. The quota accounting only holds while requests are serialised; under
parallel workers the throttle would race itself.

### Quota budget per run

| Suite | Requests | Safe on a PR? |
|---|---|---|
| `make catalog` | 0 (no network) | Yes |
| `make api` (functional) | ~15 | Yes |
| `make ratelimit` | ~12 | Yes |
| `make perf` | ~46 | Yes, alone |
| `make api` + `make perf` back to back | ~61 | Yes — the throttle parks if needed |
| `make saturate` | 130+, empties the window | **No** |

---

## 4. Saturation testing: deliberately off

Three tests (RL-08, RL-09, RL-10) prove the limiter actually *enforces* — that
the headers are not advertising a limit nobody applies, that a 429 tells a
client when to come back, and that quota is released on schedule rather than
latching until redeploy.

**What running them found.** On a window left clean for 65 seconds:

```
130 requests at concurrency 10   ->  130 x 200, zero 429
140 requests strictly sequential ->  140 x 200, zero 429
```

with `remaining` reported as 76, 95, 70, 46, 77 at requests 25/50/75/100/125 of
the sequential run — successive requests on **one reused connection** answered
by different instances, each with its own counter.

The limiter is not absent. Once a burst has depleted enough instances,
throttling does engage: RL-12 recorded its first 429 at sequential request 108
after RL-08's burst, and RL-09/RL-10 then verified the 429 is usable and that
service resumes. But **a single client sustaining well over the advertised rate
is not throttled on a fresh window**, because its traffic fragments across
per-instance counters faster than any one of them fills.

Two directions matter. As abuse protection this is much weaker than
`x-ratelimit-limit: 100` suggests — and since a 404 costs the same as a 200
(RL-05), slug enumeration is barely rate-limited at all. As a client contract
it is unusable (RL-11).

This is a product decision, not a test to make green: fixing it means moving
the limiter to shared storage (Redis or similar) so one counter serves all
instances. So RL-12 reports by default and fails only under
`rateLimit.saturation.requireEnforcement`. RL-08 was deliberately narrowed to
the assertion that holds either way — under a burst the endpoint must serve or
throttle, never 5xx — because a test that is red every run is a test that gets
muted.

They cannot be run casually. Emptying the window blocks **every other caller on
this egress IP** for up to a minute: CI, the browser suite, and anyone using
the dev site. So they are gated twice — `rateLimit.saturation.enabled` is
`false` in config, and `RUN_RATE_LIMIT_SATURATION` must be set:

```bash
make saturate          # ~2 minutes, and nobody else should be using dev
```

They belong on a nightly or weekly schedule against a quiet environment, never
in a pull-request check. `.github/workflows/perf.yml` runs the perf suite on a
schedule and leaves saturation as a manual `workflow_dispatch` input, for the
same reason.

---

## 5. Test coverage

### Implemented — rate limiting (`tests/api/tests/test_rate_limit.py`)

| ID | Case | Marker | Cost | Status |
|---|---|---|---|---|
| RL-01 | The API advertises its rate limit at all | `smoke ratelimit` | 1 | Active |
| RL-02 | `limit`/`remaining`/`reset` are internally consistent and in range | `ratelimit` | 1 | Active |
| RL-03 | The limit has not silently changed from the configured 100 | `ratelimit` | 1 | Active |
| RL-04 | Consecutive requests actually decrement `remaining` | `ratelimit` | 3 | Active |
| RL-05 | A 404 still costs a request | `ratelimit` | 2 | Active |
| RL-06 | One bucket covers the whole API, not one per endpoint | `ratelimit` | 2 | Active |
| RL-07 | `/env.js` stays outside the bucket | `ratelimit` | 1 | Active |
| RL-11 | Limiter state is consistent across instances | `ratelimit` | 8 | Reports; fails only on `requireGlobalConsistency` |
| RL-08 | A burst past the limit never 5xxs | `load` | 130 | **Opt-in** |
| RL-09 | The 429 tells a client how to back off | `load` | ≤260 | **Opt-in** |
| RL-10 | The window rolls over and service resumes | `load` | ≤260 + 65s | **Opt-in** |
| RL-12 | The advertised limit is actually enforced | `load` | ≤130 | **Opt-in**; reports, fails only on `requireEnforcement` |

RL-05 and RL-06 look like trivia and are not. Both are load-bearing for the
suite's own quota planning: if failures stopped being charged, or buckets
became per-path, the throttling in section 3 would be wrong — in RL-05's case
it would also mean slug enumeration had become free.

### Implemented — performance (`tests/api/tests/test_performance.py`)

| ID | Case | What it catches | Status |
|---|---|---|---|
| PERF-01 | First request on a fresh connection within `coldMs` | Cold-start and TLS cost, the worst first impression a field user gets | Active |
| PERF-02 | Warm p50 within budget | The median caller slowing down | Active |
| PERF-03 | Warm p95 within budget | A growing tail while the median still looks fine | Active |
| PERF-04 | No single sample breaches the hard 3 s ceiling | Same limit as API-08, asked 20 times instead of once | Active |
| PERF-05 | p95/p50 spread bounded | Bimodal latency — cold starts leaking into normal traffic — **before** either percentile budget breaks | Active |
| PERF-06 | Payload within its byte budget | A payload tripling; no functional test would notice | Active |
| PERF-07 | Compression still negotiated, ≥2× saving | Losing brotli/gzip: invisible on a laptop, very visible on rural LTE | Active |
| PERF-08 | 5 concurrent callers — p50 and max | The endpoint serialising under trivial parallelism | Active |
| PERF-09 | 404 path is not slower than the happy path | A slow error path: same quota cost, higher amplification for anyone probing | Active |
| PERF-10 | `/env.js` p95 | The file that blocks SPA boot before any other number matters | Active |

**Why PERF-08 gates p50 and max but not p95.** Five parallel callers produced
nine responses of 292–529 ms and one of 3269 ms. That outlier is the platform
starting a second instance to absorb the parallelism. With five workers over
ten samples, a p95 lands on that cold start whenever it happens — a second run
minutes later showed zero of them and a p95 of 616 ms. Gating on p95 there
would be red on a healthy deployment roughly half the time, which is how a perf
gate gets muted. p50 answers the question the test is actually asking: if
requests were queueing, the median would climb towards the serial total rather
than sitting at 332 ms. `max` bounds the worst case at something a scale-out can
reach and a queue cannot. The scale-out count is recorded in the report as
information rather than asserted, because it is a property of the platform's
scaling, not of this endpoint's code.

### Deferred, with reasons

Listing these so the gaps are choices rather than oversights.

| ID | Case | Why not yet |
|---|---|---|
| RL-15 | The limit is keyed per client IP, not shared across callers | Needs two source addresses. Partially answered by RL-11: the counter is not even consistent for one caller. Test from CI and a local run inside one window. |
| RL-12 | Authenticated callers get their own quota | Phase 2 — no authenticated endpoints in scope yet (`APP_USER`/`APP_PASSWORD` are unused). |
| RL-13 | Limiter cannot be bypassed via header spoofing (`X-Forwarded-For`) | Security test, not a performance one. Needs authorisation to attempt; belongs with a pentest scope, not a PR check. |
| RL-14 | 429 responses are not cached by the CDN | Would need a cache-poisoning probe against shared infrastructure. High blast radius for the value. |
| PERF-11 | Conditional GET (`If-None-Match`) returns 304 | Verified by hand — it works. Worth adding as a bandwidth-regression test; low priority because it saves bytes, not quota. |
| PERF-12 | Latency from a second geography | The deployment served from `bom1` on this run. A field user in the US pays different numbers. Needs a CI runner in another region. |
| PERF-13 | Sustained-load capacity ("how many concurrent callers before p95 doubles?") | Impossible under a 100/min cap. Needs the dedicated environment described in section 2. |
| PERF-14 | Asset/image delivery timing | Assets are on the SPA's critical path but served from a different origin. Belongs with the browser suite, which can measure what the page actually waits for. |
| PERF-15 | Agent session connect and first-token latency under concurrency | This is the number that actually decides whether the product is usable. It needs LiveKit sessions, not HTTP — `tests/sdk/` now records per-turn timings in report/data/livekit-sdk.*.json. Currently covered only as single-session budgets in the chat suite. |
| PERF-16 | Trend regression — this run vs the last ten | `report/data/api-perf.json` is written for exactly this. Needs somewhere to keep history; a CI artifact is not a time series. |

The biggest genuine gap is **PERF-15**. Everything in this document measures a
JSON endpoint that responds in 400 ms. The thing a technician in a quarry waits
for is an agent turn, budgeted at 45 seconds in `testbed.config.json` and
measured at 26–29 seconds. HTTP latency is not where this product's
performance risk lives — it is just where it is cheap to measure, and where a
regression can be caught before it reaches the expensive suites.

---

## 6. Running it

```bash
make ratelimit     # ~12 requests, 6s. Safe on every PR.
make perf          # ~46 requests, ~15s. Writes report/data/api-perf.json.
make perf-report   # pretty-print the last run's numbers
make saturate      # OPT-IN. Empties the window. Not on a PR.
make api           # everything except @load
```

Environment overrides, all optional:

| Variable | Effect |
|---|---|
| `RUN_RATE_LIMIT_SATURATION=true` | Enables RL-08..RL-10 |
| `RATE_LIMIT_RESERVE_FLOOR=n` | Quota the suite refuses to spend (default 15) |

Everything else — budgets, sample counts, header names, the expected limit —
is in `rateLimit` and `apiPerformance` in `config/testbed.config.json`, so
pointing the suite at another deployment stays a config edit.

## 7. Reading the report

`report/data/api-perf.json` holds every sample from the last run:

```json
{
  "measurements": [
    {"label": "product endpoint, warm", "n": 20, "p50Ms": 422.3,
     "p95Ms": 499.9, "maxMs": 539.8, "spread": 1.18}
  ],
  "notes": {
    "compression": {"encoding": "br", "ratio": 4.01},
    "rateLimit": {"requestsObserved": 46, "lowWaterRemaining": 54,
                  "windowsUsed": 2, "secondsSpentThrottled": 0.0}
  }
}
```

`lowWaterRemaining` is the one to watch. If it approaches `reserveFloor` on
ordinary runs, the suite has outgrown its quota and either the sample counts
come down or the limit goes up — before it starts failing other people's tests.
