"""
LKT auth: the LiveKit project refuses what the backend did not issue.

These talk to LiveKit with the project's API key. None of them wakes an agent:
the forged tokens are refused before a room exists, and the dispatch tests use
rooms the server API creates, which no token-borne dispatch is attached to.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta

import pytest

from lkqa import session
from lkqa.bridge import testbed

pytestmark = pytest.mark.auth

LK = testbed.judge_config()["livekit"]


async def _join(token: str) -> Exception | None:
    """None if the join succeeded (and it is immediately left), else the error."""
    import os

    from livekit import rtc

    room = rtc.Room()
    try:
        await asyncio.wait_for(room.connect(os.environ["LIVEKIT_URL"], token), 15)
    except Exception as exc:  # noqa: BLE001 - the refusal IS the result
        return exc
    await room.disconnect()
    return None


@pytest.fixture
def issued(r, admin_available) -> session.Grant:
    from lkqa import cases

    kb = cases.serial_routed_kbs()[0]
    return session.request_session(cases.caller(r, cases.serial_for(kb["id"], r)))


async def test_lkt01_a_properly_signed_token_is_accepted(admin_available):
    """The control: without it, every refusal below could be the network."""
    assert await _join(session.mint_token()) is None


async def test_lkt01_a_token_signed_with_the_wrong_secret_is_refused(admin_available):
    err = await _join(session.mint_token(secret="not-the-secret-" + uuid.uuid4().hex))
    assert err is not None, "LiveKit accepted a token signed with the wrong secret"


async def test_lkt01_an_expired_token_is_refused(admin_available):
    err = await _join(session.mint_token(ttl=timedelta(seconds=-60)))
    assert err is not None, "LiveKit accepted an expired token"


async def test_lkt01_a_token_without_roomjoin_is_refused(admin_available):
    err = await _join(session.mint_token(room_join=False))
    assert err is not None, "LiveKit accepted a token with no roomJoin grant"


async def test_lkt01_an_issued_token_cannot_be_retargeted_at_another_room(issued):
    """The attack that matters: take a real caller token and point it at
    somebody else's call. The signature must break."""
    forged = session.tamper(issued.token, video__room=f"product-someone-else-{uuid.uuid4().hex[:8]}")
    err = await _join(forged)
    assert err is not None, "a caller token with a rewritten room claim was accepted"


async def test_lkt01_an_issued_token_cannot_have_its_dispatch_rewritten(issued):
    """Rewriting the dispatch metadata would let a caller choose the serial,
    and so the manual, after the backend validated it."""
    agents = issued.dispatches
    agents[0]["metadata"] = agents[0]["metadata"].replace(
        issued.caller["serialNumber"], "K0000"
    )
    forged = session.tamper(issued.token, roomConfig__agents=agents)
    err = await _join(forged)
    assert err is not None, "a caller token with rewritten dispatch metadata was accepted"


async def test_lkt03_a_wrong_agent_name_is_accepted_and_nothing_joins(admin, report):
    """LKT-03. The failure mode that cost this repo an afternoon: an explicit
    dispatch to a name no worker owns is ACCEPTED, and then nothing happens.
    Pinned so that anyone who changes agentName sees the symptom here first."""
    room = f"qa-auth-wrongname-{uuid.uuid4().hex[:8]}"
    await admin.create_room(room)
    try:
        await admin.dispatch(room, "no-such-agent-" + uuid.uuid4().hex[:6])
        joined = await admin.wait_until(
            lambda: _has_agent(admin, room), timeout_ms=15000, poll_s=2
        )
        report.record("LKT-03", room=room, agentJoined=joined is not None)
        assert joined is None, "an agent joined a dispatch to a name no worker should own"
    finally:
        await admin.delete_room(room)


async def test_no_agent_joins_a_room_nobody_dispatched_to(admin):
    """Auto-dispatch is off: a stray room does not burn a worker. Proven by
    make probe-agent on 2026-09-28, pinned here."""
    room = f"qa-auth-nodispatch-{uuid.uuid4().hex[:8]}"
    await admin.create_room(room)
    try:
        joined = await admin.wait_until(lambda: _has_agent(admin, room), timeout_ms=15000, poll_s=2)
        assert joined is None
    finally:
        await admin.delete_room(room)


async def _has_agent(admin, room: str) -> bool:
    return any(p.kind == 4 for p in await admin.participants(room))
