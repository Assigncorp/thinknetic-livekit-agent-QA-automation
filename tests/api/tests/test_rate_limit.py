"""
Rate-limiter contract for the public API.

The limiter is a product surface, not an implementation detail. The SPA, the
agent backend and every integrator have to back off against it, and they can
only do that if the headers mean what they say. When this file fails, a client
somewhere is about to guess.

Two tiers, and the split matters:

  * RL-01..RL-07 are the CONTRACT. About a dozen requests in total, cheap
    enough to run on every PR, and they never come close to the limit. They
    assert what the headers promise and - just as importantly - which paths
    the promise covers, because the suite's own quota accounting depends on
    knowing that a 404 costs a request.

  * RL-08..RL-10 are SATURATION. They deliberately empty the window, which
    blocks every other caller on this egress IP for up to a minute: the
    browser suite, CI, and anyone clicking through the dev site by hand. They
    are off in config AND gated by RUN_RATE_LIMIT_SATURATION, and belong on a
    schedule, not in a PR check.

Verified against etnyre-dev on 2026-09-21: limit 100, window 60s, reset is a
countdown in seconds rather than a unix timestamp, and 404s and 304s both
decrement the counter.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.utils.ratelimit import partition_streams, read_state, same_stream, saturation_enabled


def _state(response, cfg):
    h = cfg["headers"]
    return read_state(
        response,
        limit_header=h["limit"],
        remaining_header=h["remaining"],
        reset_header=h["reset"],
    )


def _paired(client, first_path: str, second_path: str, cfg, what: str):
    """
    Two readings that genuinely came from the same instance's counter.

    The counter is per serverless instance (RL-11), so a naive pair of
    consecutive requests lands on one instance only about 63% of the time when
    several are warm. Retrying is what turns "we could not tell" into an
    answer; the previous version skipped instead, and a skipped test checks
    nothing.

    Fails rather than skips when every attempt hops, because at that point
    something has changed about the deployment's scaling that the rest of this
    file's assumptions rest on.
    """
    attempts = cfg["instanceHopRetries"]
    seen = []
    for _ in range(attempts):
        first = _state(client.get(first_path), cfg)
        second = _state(client.get(second_path), cfg)
        if first and second and same_stream(first, second):
            return first, second
        seen.append((first, second))

    pytest.fail(
        f"could not get a reading of {what} from the same instance as its "
        f"baseline in {attempts} attempts. Observed pairs: "
        f"{[(a.remaining if a else None, b.remaining if b else None) for a, b in seen]}. "
        f"The deployment appears to be spread across more instances than "
        f"rateLimit.instanceHopRetries allows for - raise it, or investigate"
    )


def _requires_saturation(cfg) -> None:
    if not saturation_enabled(cfg["saturation"]["enabled"]):
        pytest.skip(
            "saturation tests are opt-in: they empty the shared window for up to "
            "a minute. Enable with RUN_RATE_LIMIT_SATURATION=true (see "
            "docs/api-test-strategy.md)"
        )


# --------------------------------------------------------------------------
# RL-01..RL-07 - the contract. Cheap, safe on every PR.
# --------------------------------------------------------------------------


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.ratelimit
def test_api_advertises_its_rate_limit(client, product_path, rate_limit_config):
    """RL-01: a client that cannot see the limit can only discover it by
    tripping it, in production, at the worst moment."""
    state = _state(client.get(product_path), rate_limit_config)
    assert state is not None, (
        f"{product_path} returned no rate-limit headers. Either the limiter was "
        f"removed - in which case the suite's quota accounting is now needlessly "
        f"conservative - or it is now invisible to clients, which is worse."
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_rate_limit_headers_are_internally_consistent(client, product_path, rate_limit_config):
    """RL-02: the three values have to make sense together, or backoff logic
    built on them does not."""
    state = _state(client.get(product_path), rate_limit_config)
    window = rate_limit_config["windowSeconds"]

    assert state.limit > 0, f"a limit of {state.limit} would reject every request"
    assert 0 <= state.remaining <= state.limit, f"remaining out of range: {state}"
    assert 0 < state.reset_s <= window, (
        f"reset is {state.reset_s}s against a declared {window}s window. If this "
        f"is a unix timestamp rather than a countdown, every client that sleeps "
        f"on it will sleep for 56 years"
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_the_limit_has_not_silently_changed(client, product_path, rate_limit_config):
    """
    RL-03: drift detector.

    Not a check that 100 is the right number - that is a product decision. It
    is a check that the number this suite paces itself against is still the
    number the server is enforcing. Halve the limit without anyone noticing and
    the first symptom is the browser suite failing on unrelated assertions.
    """
    state = _state(client.get(product_path), rate_limit_config)
    expected = rate_limit_config["expectedLimit"]
    assert state.limit == expected, (
        f"the limit moved from {expected} to {state.limit}. Update "
        f"rateLimit.expectedLimit in config/testbed.config.json, and re-check "
        f"apiPerformance.samples and rateLimit.reserveFloor against the new ceiling"
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_consecutive_requests_consume_the_window(client, product_path, rate_limit_config):
    """
    RL-04: `remaining` actually counts down.

    A limiter whose counter is pinned - a caching layer in front of it serving
    one header value to everybody, say - looks perfectly healthy in a single
    response and tells clients nothing at all.

    Judged on the longest single-instance stream in a short burst rather than
    on two consecutive readings, because the counter is per instance (RL-11).
    When several instances are warm, two consecutive readings routinely come
    from different counters and the second is HIGHER - which is not a rollover
    and not a defect, just a different instance answering. The earlier version
    of this test read that as a rollover and skipped itself, which meant it
    stopped checking precisely when the deployment was busiest.
    """
    readings = [_state(client.get(product_path), rate_limit_config) for _ in range(6)]
    streams = partition_streams([r for r in readings if r])
    longest = max(streams, key=len)

    assert len(longest) >= 3, (
        f"could not get 3 readings from one instance in 6 requests - "
        f"{len(streams)} separate limiter states appeared: "
        f"{[[r.remaining for r in s] for s in streams]}. Raise the burst size, "
        f"or the deployment is spread across more instances than this can follow"
    )
    counts = [r.remaining for r in longest]
    assert all(b < a for a, b in zip(counts, counts[1:])), (
        f"remaining did not fall consistently within one instance's counter: "
        f"{counts}. The limiter is not tracking this client's requests"
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_a_404_still_costs_a_request(client, product_path, unknown_product_path, rate_limit_config):
    """
    RL-05: failures are charged, and the suite budgets on the assumption that
    they are.

    This is the right behaviour - a limiter that only counts successes is a
    free enumeration oracle for anyone probing for valid slugs. It is asserted
    here because the fail-closed tests in test_public_product.py spend quota
    they never mention, and if that ever stopped being true the reserve floor
    would be wrong in the other direction.
    """
    before, after = _paired(
        client, product_path, unknown_product_path, rate_limit_config, "a 404"
    )
    assert after.remaining == before.remaining - 1, (
        f"a 404 moved the counter from {before.remaining} to {after.remaining}. "
        f"If failed lookups are now free, an attacker can enumerate slugs without "
        f"limit - and the suite's quota planning is based on them not being"
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_one_bucket_covers_the_whole_api(
    client, product_path, unknown_org_slug, product_slug, rate_limit_config
):
    """
    RL-06: the limit is per-client, not per-endpoint.

    Worth pinning down because the two readings differ entirely in what they
    mean for the suite. One shared bucket means the whole suite shares 100 a
    minute and has to pace itself. Per-endpoint buckets would mean each test
    file has its own, and all the throttling here would be dead weight.
    """
    from src.clients.product_client import ProductClient

    before, other = _paired(
        client,
        product_path,
        ProductClient.product_path(unknown_org_slug, product_slug),
        rate_limit_config,
        "a different org path",
    )
    assert other.remaining == before.remaining - 1, (
        f"a request to a different org path did not draw on the same bucket "
        f"({before} then {other}). If buckets are now per-path, the suite's "
        f"throttling is over-cautious and can be relaxed"
    )
    assert other.limit == before.limit


@pytest.mark.live
@pytest.mark.ratelimit
@pytest.mark.parametrize("path", ["/env.js"])
def test_unlimited_paths_stay_outside_the_bucket(client, path, rate_limit_config):
    """
    RL-07: /env.js is a static asset and carries no limiter headers.

    The SPA fetches it on every single page load, before anything else. Putting
    it behind the same 100-a-minute bucket as the API would make a busy moment
    - or a CI run - break page loads rather than slow them, and it would make
    the UI suite's own page loads eat the API suite's quota.
    """
    assert path in rate_limit_config["unlimitedPaths"], f"{path} is not declared unlimited"
    response = client.get(path)
    assert response.status_code == 200
    assert _state(response, rate_limit_config) is None, (
        f"{path} has moved behind the rate limiter. Every page load now spends "
        f"API quota, and a CI run can take the dev site's own page loads down"
    )


@pytest.mark.live
@pytest.mark.ratelimit
def test_limiter_state_is_consistent_across_instances(
    client, product_path, rate_limit_config, recorder
):
    """
    RL-11: is `x-ratelimit-remaining` a number a client can actually act on?

    MEASURED 2026-09-21, and this is the finding: the limiter's counter lives
    per serverless instance, not per client. With one instance warm, 25
    consecutive requests decrement cleanly from 99 to 75. With several warm -
    which the concurrency probe in test_performance.py causes by itself -
    independent counters interleave:

        stream A:  65 64 63 62 61 60 59 58 57 56 ...   resetting in 23s
        stream B:  89       77 76             75 ...   resetting in  8s

    Two consequences, and the second is the one that matters.

    The effective ceiling is 100 x (warm instances), not 100. The suite still
    paces itself against 100 because that is the only figure it can observe
    and it errs safe.

    More importantly, the headers stop being actionable. Their entire purpose
    is to let a client back off before it is throttled, and a client that
    reads `remaining: 51` may get `74` on its next request and `8` on the one
    after. It cannot distinguish "I have plenty left" from "I am one request
    from a 429 on the instance I happen to land on next". That is a real
    weakness in a public contract, and it is worth someone deciding about
    rather than discovering during an incident.

    Reports by default; fails only when rateLimit.requireGlobalConsistency is
    on. Off because this is a property of the platform's scaling rather than
    of this deployment's code, and a gate that goes red whenever traffic picks
    up is a gate that gets muted within a fortnight.
    """
    readings = [_state(client.get(product_path), rate_limit_config) for _ in range(8)]
    streams = partition_streams([r for r in readings if r])

    observed = {
        "requests": len(readings),
        "distinctStates": len(streams),
        "streams": [[r.remaining for r in s] for s in streams],
    }
    recorder.note("limiterConsistency", observed)
    if len(streams) > 1:
        print(
            f"\n[rate limit] {len(streams)} independent limiter states across "
            f"{len(readings)} requests: {observed['streams']}. The effective "
            f"ceiling is higher than the advertised {rate_limit_config['expectedLimit']}, "
            f"and x-ratelimit-remaining is not usable for client backoff."
        )

    if not rate_limit_config["requireGlobalConsistency"]:
        pytest.skip(
            f"observed {len(streams)} limiter state(s); reporting only. Set "
            f"rateLimit.requireGlobalConsistency to fail on this - see the docstring"
        )

    assert len(streams) == 1, (
        f"{len(streams)} independent rate-limit counters answered {len(readings)} "
        f"requests from one client: {observed['streams']}. A client cannot back "
        f"off against a counter that changes depending on which instance answers"
    )


# --------------------------------------------------------------------------
# RL-08..RL-10 - saturation. Opt-in: these empty the shared window.
# --------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.ratelimit
@pytest.mark.load
def test_the_endpoint_survives_a_burst(client, product_path, rate_limit_config, recorder):
    """
    RL-08: a burst well past the advertised limit does not break the endpoint.

    Deliberately NOT "a burst produces a 429" - that is RL-12, and it does not
    currently happen. What this asserts is the thing that must hold either
    way: whether the limiter throttles or waves the traffic through, nothing
    5xxs. A limiter that fails open is a weakness; a limiter that 500s under
    pressure turns a throttle into an outage, which is strictly worse.
    """
    _requires_saturation(rate_limit_config)
    sat = rate_limit_config["saturation"]

    statuses: list[int] = []

    def fire(_: int):
        return client.get(product_path)

    with ThreadPoolExecutor(max_workers=sat["concurrency"]) as pool:
        for response in pool.map(fire, range(sat["maxRequests"])):
            statuses.append(response.status_code)

    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    recorder.note("burst", {"requests": len(statuses), "statuses": counts})
    print(f"\n[rate limit] burst of {len(statuses)} at concurrency {sat['concurrency']}: {counts}")

    server_errors = [s for s in statuses if s >= 500]
    assert not server_errors, (
        f"the endpoint returned {len(server_errors)} server error(s) under a burst "
        f"of {len(statuses)}: {counts}. Under pressure it must either serve or "
        f"throttle, never fail"
    )
    assert set(counts) <= {200, sat["expectStatus"]}, (
        f"unexpected statuses under load: {counts}"
    )


@pytest.mark.live
@pytest.mark.ratelimit
@pytest.mark.load
def test_the_advertised_limit_is_actually_enforced(
    client, product_path, rate_limit_config, recorder
):
    """
    RL-12: does `x-ratelimit-limit: 100` mean anything to a single client?

    MEASURED 2026-09-21, on a window left clean for 65 seconds beforehand:

        130 requests at concurrency 10   ->  130x 200, zero 429
        140 requests strictly sequential ->  140x 200, zero 429

    with `remaining` reported as 76, 95, 70, 46, 77 at requests 25/50/75/100/
    125 of the sequential run - successive requests on ONE reused connection
    being answered by different instances, each with its own counter.

    The limiter is not absent: 429s do appear once enough instances have been
    depleted, which is why RL-09 and RL-10 have something to assert on after a
    heavy run. But a single client sustaining well over the advertised rate is
    not throttled, because its traffic fragments across per-instance counters
    faster than any one of them fills. The advertised figure overstates the
    real protection by a large and variable factor.

    That matters in two directions. As abuse protection it is much weaker than
    it looks - the 404 path costs the same as the happy path (RL-05), so slug
    enumeration is barely rate-limited at all. And as a client contract it is
    unusable, which is RL-11.

    Reports by default and fails only under saturation.requireEnforcement,
    because fixing it means moving the limiter to shared storage - a product
    decision, not a test to make green.
    """
    _requires_saturation(rate_limit_config)
    sat = rate_limit_config["saturation"]

    throttled_at: int | None = None
    for i in range(1, sat["maxRequests"] + 1):
        if client.get(product_path).status_code == sat["expectStatus"]:
            throttled_at = i
            break

    recorder.note(
        "enforcement",
        {
            "advertisedLimit": rate_limit_config["expectedLimit"],
            "sequentialRequests": sat["maxRequests"],
            "throttledAtRequest": throttled_at,
        },
    )
    if throttled_at is None:
        print(
            f"\n[rate limit] {sat['maxRequests']} sequential requests, no 429. The "
            f"advertised limit of {rate_limit_config['expectedLimit']}/minute is not "
            f"enforced for a single client - see RL-11 and the docstring here."
        )

    if not sat["requireEnforcement"]:
        pytest.skip(
            f"throttled at request {throttled_at}"
            if throttled_at
            else f"NOT throttled in {sat['maxRequests']} sequential requests - "
            f"reporting only. Set rateLimit.saturation.requireEnforcement to fail on this"
        )

    assert throttled_at is not None, (
        f"{sat['maxRequests']} sequential requests produced no "
        f"{sat['expectStatus']} against an advertised limit of "
        f"{rate_limit_config['expectedLimit']}. The limit is not enforced"
    )


def _drive_to_429(client, path: str, cfg):
    """
    Get a 429 to inspect, or None.

    Concurrency first to spread depletion across instances, then a sequential
    pass to find one that is already exhausted. Needed because, per RL-12, a
    single client cannot reliably reach the limit any other way.
    """
    sat = cfg["saturation"]

    def fire(_: int):
        return client.get(path)

    with ThreadPoolExecutor(max_workers=sat["concurrency"]) as pool:
        for response in pool.map(fire, range(sat["maxRequests"])):
            if response.status_code == sat["expectStatus"]:
                return response

    for _ in range(sat["maxRequests"]):
        response = client.get(path)
        if response.status_code == sat["expectStatus"]:
            return response
    return None


@pytest.mark.live
@pytest.mark.ratelimit
@pytest.mark.load
def test_the_429_tells_a_client_how_to_behave(client, product_path, rate_limit_config):
    """
    RL-09: when the limiter does fire, the response is usable.

    A 429 has one job beyond saying no: telling the caller when to come back.
    Without that a client either retries immediately - making it worse - or
    picks a number out of the air.

    Skips rather than fails when no 429 can be provoked, because that is RL-12's
    finding to report, not this one's. Asserting it here too would report one
    defect as two.
    """
    _requires_saturation(rate_limit_config)
    sat = rate_limit_config["saturation"]

    response = _drive_to_429(client, product_path, rate_limit_config)
    if response is None:
        pytest.skip(
            "could not provoke a 429 to inspect - see RL-12, the advertised limit "
            "is not enforced for a single client"
        )

    assert "retry-after" in response.headers or _state(response, rate_limit_config), (
        "the 429 carries neither Retry-After nor rate-limit headers, so a client "
        "has no way to know when to retry except by guessing"
    )
    if sat["requireRetryAfter"]:
        assert "retry-after" in response.headers, (
            "rateLimit.saturation.requireRetryAfter is on but the 429 has no "
            "Retry-After header"
        )

    state = _state(response, rate_limit_config)
    if state:
        assert state.remaining == 0, f"a 429 reported {state.remaining} requests still available"


@pytest.mark.live
@pytest.mark.ratelimit
@pytest.mark.load
def test_the_window_rolls_over_and_service_resumes(client, product_path, rate_limit_config):
    """
    RL-10: being throttled is temporary.

    The failure this guards against is a limiter that latches - a counter that
    never resets, or resets only on redeploy - which turns a minute of traffic
    into an outage that lasts until somebody notices. It is also the reason the
    cooldown is asserted rather than assumed: every other test in the suite is
    written on the premise that quota comes back.
    """
    _requires_saturation(rate_limit_config)
    sat = rate_limit_config["saturation"]

    if _drive_to_429(client, product_path, rate_limit_config) is None:
        pytest.skip("could not provoke a 429 to recover from - see RL-12")

    time.sleep(sat["cooldownSeconds"])

    recovered = client.get(product_path)
    assert recovered.status_code == 200, (
        f"still {recovered.status_code} after waiting {sat['cooldownSeconds']}s - "
        f"longer than the declared {rate_limit_config['windowSeconds']}s window. "
        f"The limiter is not releasing quota on schedule"
    )
    state = _state(recovered, rate_limit_config)
    if state:
        assert state.remaining > 0, f"window rolled over but reported {state}"
