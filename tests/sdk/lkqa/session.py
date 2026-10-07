"""
Getting a session the way a real caller gets one.

The product page never talks to LiveKit's server API. It POSTs the "Before we
start" form to the product backend's assistant-session endpoint and gets back a
`server_url` and a `participant_token`. That token does everything: it is
scoped to a fresh room, and its `roomConfig.agents` entry dispatches the agent
worker into that room the moment someone joins, carrying the caller context
(serial, name, company, phone) as dispatch metadata. VERIFIED 2026-09-28 by
decoding the token the page was issued.

So the suite does exactly that, and nothing here needs LiveKit credentials. The
API key is only used by `mint_token`, for the auth tests that must prove a token
the backend did NOT issue is refused.

Minting a token starts nothing. Token dispatch fires when the room is created
by the first join, so the contract tests can mint freely without ever waking an
agent - they cost rate-limit quota and nothing else.
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from .bridge import testbed


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover - certifi is a hard dependency
        return ssl.create_default_context()


def base_url() -> str:
    return os.getenv("BASE_URL", "https://etnyre-dev.thinknetic.app").rstrip("/")


def session_path(product: str | None = None, org: str | None = None) -> str:
    template = testbed.judge_config()["livekit"]["sessionPath"]
    return template.format(
        org=org or os.getenv("ORG_SLUG", "e"),
        product=product or os.getenv("PRODUCT_SLUG", "chip-spreader"),
    )


def decode_claims(token: str) -> dict[str, Any]:
    """The JWT payload, unverified. We are reading what we were given, not
    trusting it - LiveKit verifies the signature when we join."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


@dataclass
class HttpResult:
    status: int
    body: Any
    ratelimit_remaining: int | None
    elapsed_ms: int


@dataclass
class Grant:
    """What the endpoint hands a caller: where to connect, and the token."""

    server_url: str
    token: str
    claims: dict[str, Any] = field(default_factory=dict)
    caller: dict[str, str] = field(default_factory=dict)

    @property
    def room(self) -> str:
        return self.claims["video"]["room"]

    @property
    def identity(self) -> str:
        return self.claims["sub"]

    @property
    def dispatches(self) -> list[dict[str, Any]]:
        return list((self.claims.get("roomConfig") or {}).get("agents") or [])

    @property
    def dispatch_metadata(self) -> dict[str, Any]:
        agents = self.dispatches
        return json.loads(agents[0]["metadata"]) if agents else {}

    @property
    def ttl_seconds(self) -> int:
        return int(self.claims["exp"]) - int(self.claims["nbf"])


def _post_json(url: str, body: bytes) -> HttpResult:
    req = urllib.request.Request(
        url, data=body, headers={"content-type": "application/json"}, method="POST"
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=30) as resp:
            status, raw, headers = resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as exc:
        status, raw, headers = exc.code, exc.read(), exc.headers
    elapsed = int((time.monotonic() - started) * 1000)
    names = testbed.config()["rateLimit"]["headers"]
    try:
        parsed: Any = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = raw.decode("utf-8", "replace")

    def _int(name: str) -> int | None:
        value = headers.get(names[name])
        return int(value) if value is not None and value.lstrip("-").isdigit() else None

    return HttpResult(status, parsed, _int("remaining"), elapsed)


_last_remaining: int | None = None
_last_seen: float = 0.0


def _respect_rate_limit() -> None:
    """Park rather than spend the last of the shared window.

    The endpoint shares the API's 100/minute bucket with the API suite, the
    browser suite and anyone clicking through dev. Below rateLimit.reserveFloor
    we wait out the window instead of leaving a later test to fail on a 429
    that has nothing to do with it - same rule as api/src/utils/ratelimit.py.
    """
    floor = int(testbed.config()["rateLimit"]["reserveFloor"])
    window = int(testbed.config()["rateLimit"]["windowSeconds"])
    if _last_remaining is not None and _last_remaining <= floor:
        wait = max(0.0, window - (time.monotonic() - _last_seen)) + 1
        print(f"[lkqa] rate-limit window low ({_last_remaining} left) - waiting {wait:.0f}s")
        time.sleep(wait)


def post_session(body: dict[str, Any] | None, *, product: str | None = None) -> HttpResult:
    """One raw call to the session endpoint - for the contract tests, which
    need the failures as much as the successes."""
    global _last_remaining, _last_seen
    _respect_rate_limit()
    data = b"" if body is None else json.dumps(body).encode()
    result = _post_json(base_url() + session_path(product), data)
    if result.ratelimit_remaining is not None:
        _last_remaining, _last_seen = result.ratelimit_remaining, time.monotonic()
    return result


def intake_body(caller: dict[str, str]) -> dict[str, str]:
    """The form's four fields, under the names the page sends them as."""
    return {
        "serial_number": caller["serialNumber"],
        "customer_name": caller["customerName"],
        "company_name": caller["companyName"],
        "phone": caller["phone"],
    }


def request_session(caller: dict[str, str], *, product: str | None = None) -> Grant:
    result = post_session(intake_body(caller), product=product)
    if result.status != 200 or not isinstance(result.body, dict):
        raise RuntimeError(
            f"the session endpoint refused a valid caller: HTTP {result.status} {result.body!r}. "
            f"Nothing LiveKit-side has been tried yet - this is the product backend."
        )
    token = result.body["participant_token"]
    return Grant(
        server_url=result.body["server_url"],
        token=token,
        claims=decode_claims(token),
        caller=caller,
    )


# ---------------------------------------------------------------------------
# Tokens we mint ourselves - auth tests only
# ---------------------------------------------------------------------------


def credentials_available() -> tuple[bool, str]:
    missing = [n for n in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET") if not os.getenv(n)]
    if missing:
        return False, f"{', '.join(missing)} not set in .env"
    return True, ""


def mint_token(
    *,
    room: str | None = None,
    secret: str | None = None,
    ttl: timedelta = timedelta(minutes=5),
    room_join: bool = True,
    identity: str | None = None,
) -> str:
    """A token signed with the project key - or a deliberately wrong one."""
    from livekit import api

    return (
        api.AccessToken(os.environ["LIVEKIT_API_KEY"], secret or os.environ["LIVEKIT_API_SECRET"])
        .with_identity(identity or f"qa-auth-{uuid.uuid4().hex[:8]}")
        .with_ttl(ttl)
        .with_grants(
            api.VideoGrants(
                room_join=room_join,
                room=room or f"qa-auth-{uuid.uuid4().hex[:8]}",
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )


def tamper(token: str, **claim_overrides: Any) -> str:
    """Rewrite a token's payload and keep its original signature."""
    header, payload, signature = token.split(".")
    claims = decode_claims(token)
    for dotted, value in claim_overrides.items():
        node = claims
        *parents, leaf = dotted.split("__")
        for key in parents:
            node = node.setdefault(key, {})
        node[leaf] = value
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{header}.{forged}.{signature}"
