"""
Latency and payload budgets for the public API.

Risk #5 on the test plan - "latency makes the agent unusable in the field" -
and the layer where it is cheapest to measure. The existing check (API-08)
times one request against 3s. One request is a coin toss: it catches an outage
and nothing else. This file measures the distribution instead, and splits the
first request of a session out of it, because those two numbers fail for
completely different reasons and a budget that mixes them tells you neither.

Baselines from etnyre-dev, 2026-09-21:

    first request of a session   2090 ms   (TLS + serverless cold start)
    warm p50                      410 ms
    warm p95                     1020 ms
    404 path                      380 ms
    /env.js                    200-400 ms
    payload                  22710 bytes raw, 5822 gzipped

Budgets in config sit at roughly 2x those, which is loose on purpose: this
runs against a shared dev deployment with other people on it, and a perf gate
that flaps gets muted within a fortnight. Every run writes its numbers to
report/data/api-perf.json so the budgets can be re-based on evidence rather than
on the first figure anybody wrote down.

THE CONSTRAINT, and why this file looks the way it does: the API allows 100
requests a minute for the entire suite, counting failures. This is therefore
sampling, not load generation. `bucket.reserve()` parks the suite when a
measurement would dig into the reserve floor, so a percentile can never be the
reason the functional tests behind it get a 429. See docs/api-test-strategy.md
for what would have to change before reaching for k6.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from src.utils.perf import Samples, measure

pytestmark = [pytest.mark.live, pytest.mark.perf]


@pytest.fixture(scope="module")
def warm(perf_client, product_path, perf_config, bucket, recorder) -> Samples:
    """
    The warm distribution, measured once and shared by every percentile test
    below.

    Module-scoped because the samples cost real quota: three tests each taking
    their own set of 20 would spend more than half a window to answer three
    questions about the same distribution.
    """
    n = perf_config["samples"]
    warmups = perf_config["warmupRequests"]
    bucket.reserve(n + warmups, why="warm latency distribution")

    for _ in range(warmups):
        perf_client.get(product_path)

    samples = Samples("product endpoint, warm")
    for i in range(n):
        sample, response = measure(f"warm-{i:02d}", lambda: perf_client.get(product_path))
        assert response.status_code == 200, (
            f"sample {i} returned {response.status_code}; a latency distribution "
            f"over failed requests measures nothing. Body: {response.text[:200]}"
        )
        samples.add(sample)

    recorder.record(samples)
    print(f"\n[perf] {samples.describe()}")
    return samples


# --------------------------------------------------------------------------
# PERF-01..PERF-05 - the product endpoint's latency
# --------------------------------------------------------------------------


def test_first_request_of_a_session_is_tolerable(
    base_url, product_path, perf_config, bucket, recorder
):
    """
    PERF-01: the cold path - a first request on a brand-new connection.

    Its own client, because a connection reused from another fixture has
    already paid the TLS handshake and would measure the wrong thing.

    What this catches honestly: connection setup, plus a serverless cold start
    WHEN the deployment has actually gone cold. Measured 2090ms on a genuinely
    cold deployment and 783ms when the function was already warm, against a
    warm-connection p50 of 422ms. So it is a ceiling on the worst first
    impression, not a guaranteed cold-start measurement - the budget is sized
    for the cold case because that is the one a field technician opening the
    page on a phone actually pays, and averaging it into the warm distribution
    would hide it completely.
    """
    import httpx

    bucket.reserve(1, why="cold-path measurement")
    budget = perf_config["budgets"]["coldMs"]

    with httpx.Client(base_url=base_url, timeout=30.0, follow_redirects=False) as fresh:
        sample, response = measure("cold", lambda: fresh.get(product_path))
    assert response.status_code == 200, response.text[:200]
    recorder.note("coldMs", sample.elapsed_ms)
    assert sample.elapsed_ms <= budget, (
        f"the first request of a session took {sample.elapsed_ms:.0f}ms against a "
        f"{budget}ms budget. This is the number a technician on a phone in the "
        f"field pays, not the warm one"
    )


def test_typical_response_is_fast(warm, perf_config):
    """PERF-02: p50 - what the median caller gets."""
    warm.assert_within(perf_config["budgets"]["warmP50Ms"], at="p50")


def test_slow_tail_stays_bounded(warm, perf_config):
    """
    PERF-03: p95 - what the unlucky one in twenty gets.

    The one worth gating on. A median that holds while the tail grows is the
    normal shape of an endpoint under growing load, and the median will keep
    looking fine right up until it does not.
    """
    warm.assert_within(perf_config["budgets"]["warmP95Ms"], at="p95")


def test_no_single_response_breaches_the_hard_ceiling(warm, perf_config):
    """
    PERF-04: the absolute ceiling every caller is entitled to.

    Deliberately the same 3000ms as budgets.apiResponseMs, which API-08 already
    uses on a single request. Two different hard limits for one endpoint would
    be a contradiction rather than a strategy; this one just asks the question
    twenty times instead of once.
    """
    warm.assert_within(perf_config["budgets"]["maxMs"], at="max")


def test_latency_is_not_bimodal(warm, perf_config):
    """
    PERF-05: consistency, measured as p95/p50.

    A warm endpoint sits near 1. When cold starts begin interleaving with warm
    responses - the usual first symptom of a serverless deployment running out
    of warm instances - this climbs long before either percentile budget is
    breached. It is the early warning the percentiles are not.
    """
    limit = perf_config["maxSpread"]
    assert warm.spread <= limit, (
        f"p95/p50 is {warm.spread:.1f} against a limit of {limit}. Responses are "
        f"splitting into fast and slow groups rather than clustering, which "
        f"usually means cold starts are leaking into normal traffic.\n"
        f"  {warm.describe()}"
    )


# --------------------------------------------------------------------------
# PERF-06..PERF-07 - payload weight
# --------------------------------------------------------------------------


def test_payload_stays_within_its_weight_budget(perf_client, product_path, perf_config, bucket, recorder):
    """
    PERF-06: bytes on the wire.

    Latency at the server is only half of what the field sees. This payload is
    22.2KB and hydrates the page; on a rural LTE connection the difference
    between that and 200KB is the difference between a usable page and a blank
    one. Nothing else in the suite would notice the payload tripling - every
    functional assertion would still pass.
    """
    bucket.reserve(1, why="payload size")
    budget = perf_config["budgets"]["payloadBytes"]
    sample, response = measure("payload", lambda: perf_client.get(product_path))
    assert response.status_code == 200
    recorder.note("payloadBytes", sample.bytes_down)
    assert sample.bytes_down <= budget, (
        f"the product payload is {sample.bytes_down / 1024:.1f}KB against a "
        f"{budget / 1024:.0f}KB budget. It is on the SPA's critical path"
    )


def test_payload_is_compressed_on_the_wire(perf_client, product_path, perf_config, bucket, recorder):
    """
    PERF-07: compression is still on.

    22710 bytes raw against 5822 gzipped, a 3.9x saving on the page's critical
    path. Losing it would fail no functional test and would be invisible on a
    developer's laptop. It would be extremely visible on a phone in a quarry.
    """
    bucket.reserve(2, why="compression check")
    minimum = perf_config["minCompressionRatio"]

    compressed = perf_client.get(product_path, headers={"accept-encoding": "gzip, br"})
    assert compressed.status_code == 200
    encoding = compressed.headers.get("content-encoding", "")
    assert encoding, (
        "the product payload came back uncompressed even though the client asked "
        "for gzip. Every field caller is now downloading roughly 4x the bytes"
    )

    on_the_wire = int(compressed.headers.get("content-length", 0)) or len(compressed.content)
    uncompressed = len(perf_client.get(product_path, headers={"accept-encoding": "identity"}).content)
    ratio = uncompressed / on_the_wire if on_the_wire else 0
    recorder.note("compression", {"encoding": encoding, "raw": uncompressed, "wire": on_the_wire,
                                  "ratio": round(ratio, 2)})
    assert ratio >= minimum, (
        f"compression is only saving {ratio:.1f}x ({uncompressed} -> {on_the_wire} "
        f"bytes) against a minimum of {minimum}x"
    )


# --------------------------------------------------------------------------
# PERF-08..PERF-10 - the paths a budget usually forgets
# --------------------------------------------------------------------------


def test_concurrent_callers_do_not_degrade_the_endpoint(
    perf_client, product_path, perf_config, bucket, recorder
):
    """
    PERF-08: several callers at once, which is what the endpoint actually gets.

    Ten requests across five workers - a tenth of the window, nowhere near
    load. It is not asking how much traffic the endpoint can take; it is asking
    whether it SERIALISES. An endpoint that handles ten parallel callers by
    queueing them answers every functional test correctly and is unusable the
    moment two technicians open the page together.

    Gated on p50 and max, not p95, and that is the whole design of this test.
    MEASURED 2026-09-21: five parallel callers produced nine responses between
    292ms and 529ms and one of 3269ms. The outlier is the platform starting a
    second instance to absorb the parallelism, and with five workers over ten
    samples a p95 lands on that cold start every single time - so a p95 budget
    here would be a permanently red gate on a healthy deployment, which is how
    a perf gate gets muted within a fortnight.

    p50 answers the real question: if requests were queueing behind one
    another, the median would climb towards the serial total, not sit at
    345ms. max bounds the worst case at something a scale-out can reach and a
    queue cannot. The outlier count is recorded rather than asserted, because
    it is a property of the platform's scaling, not of this endpoint's code.
    """
    conc = perf_config["concurrency"]
    total = conc["workers"] * conc["requestsPerWorker"]
    bucket.reserve(total, why="concurrency probe")

    samples = Samples(f"product endpoint, {conc['workers']} concurrent")

    def one(i: int):
        return measure(f"conc-{i:02d}", lambda: perf_client.get(product_path))

    with ThreadPoolExecutor(max_workers=conc["workers"]) as pool:
        for sample, response in pool.map(one, range(total)):
            assert response.status_code == 200, (
                f"a concurrent request returned {response.status_code}. If this is "
                f"429 the probe outran its quota reservation; anything else is the "
                f"endpoint failing under trivial parallelism"
            )
            samples.add(sample)

    recorder.record(samples)
    warm_ceiling = perf_config["budgets"]["maxMs"]
    scaled_out = [t for t in samples.times if t > warm_ceiling]
    recorder.note("concurrencyScaleOuts", {"n": len(scaled_out), "ms": [round(t) for t in scaled_out]})
    print(f"\n[perf] {samples.describe()} ({len(scaled_out)} scale-out cold start(s))")

    samples.assert_within(perf_config["budgets"]["concurrentP50Ms"], at="p50")
    samples.assert_within(perf_config["budgets"]["concurrentMaxMs"], at="max")


def test_the_error_path_is_not_slower_than_the_happy_path(
    perf_client, unknown_product_path, perf_config, bucket, recorder
):
    """
    PERF-09: 404s answer quickly.

    A slow error path is the one nobody measures and the one that hurts most:
    it costs the same rate-limit quota as a success, and if a miss is expensive
    to serve then anyone probing for valid slugs is doing far more damage per
    request than a legitimate caller. Measured at 380ms, i.e. the same as a
    200, which is what it should be.
    """
    n = max(5, perf_config["samples"] // 4)
    bucket.reserve(n, why="404 latency")

    samples = Samples("unknown product, 404")
    for i in range(n):
        sample, response = measure(f"404-{i:02d}", lambda: perf_client.get(unknown_product_path))
        assert response.status_code == 404, (
            f"the fail-closed path returned {response.status_code}, not 404 - "
            f"this is measuring the wrong thing"
        )
        samples.add(sample)

    recorder.record(samples)
    print(f"\n[perf] {samples.describe()}")
    samples.assert_within(perf_config["budgets"]["notFoundP95Ms"], at="p95")


def test_runtime_config_loads_quickly(perf_client, perf_config, bucket, recorder):
    """
    PERF-10: /env.js, which blocks everything.

    The SPA cannot decide which backend it is talking to until this lands, so
    its latency is added to every single page load before any of the numbers
    above are even reached. It sits outside the rate limiter (RL-07), so
    measuring it costs no quota - the reserve call here is defensive, in case
    that ever changes.
    """
    n = max(5, perf_config["samples"] // 4)
    bucket.reserve(n, why="/env.js latency")

    samples = Samples("/env.js")
    for i in range(n):
        sample, response = measure(f"env-{i:02d}", lambda: perf_client.get("/env.js"))
        assert response.status_code == 200
        samples.add(sample)

    recorder.record(samples)
    print(f"\n[perf] {samples.describe()}")
    samples.assert_within(perf_config["budgets"]["runtimeConfigP95Ms"], at="p95")
