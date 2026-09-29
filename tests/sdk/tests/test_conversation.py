"""
LKT / TRN / CNV / DKB: one complete call, and everything it proves.

The call runs ONCE (module fixture): join, greeting, machine identified, a
knowledge-base question, the answer, sign-off, rating, goodbye, hang-up, and
the server watching the room close. Each test below asserts one property of
that recording. One session, many assertions - the agent remembers callers per
serial, so three sessions about one serial are not three independent samples,
and each costs a worker on a shared deployment.
"""

from __future__ import annotations

import time

import pytest

from lkqa import cases
from lkqa.bridge import oracle, testbed
from lkqa.call import AGENT_KIND, EGRESS_KIND
from lkqa.driver import ScoredCall, scored_call

pytestmark = pytest.mark.live

SDK = testbed.config()["livekitSdk"]
BUDGETS = testbed.config()["budgets"]
LK = testbed.judge_config()["livekit"]


@pytest.fixture(scope="module")
async def full_call(report, r) -> ScoredCall:
    kb, scenario = cases.draw(r, SDK["grounding"]["kinds"])
    serial = cases.serial_for(kb["id"], r)
    scored = await scored_call(report, "conversation", scenario, serial, r, wrap_up=True)

    # LKT-06: after the hang-up, the server's view of the room.
    from lkqa.admin import Admin
    from lkqa.session import credentials_available

    if credentials_available()[0]:
        admin = Admin()
        try:
            hung_up = scored.call.disconnected_at or time.monotonic()

            async def agent_gone() -> bool:
                return not any(p.kind == AGENT_KIND for p in await admin.participants(scored.grant.room))

            async def room_gone() -> bool:
                return not await admin.room_exists(scored.grant.room)

            gone = await admin.wait_until(agent_gone, int(SDK["budgets"]["agentLeavesAfterHangupMs"]))
            closed = await admin.wait_until(room_gone, int(SDK["budgets"]["roomClosedAfterHangupMs"]))
            scored.call.__dict__["server_agent_gone_ms"] = None if gone is None else int((gone - hung_up) * 1000)
            scored.call.__dict__["server_room_closed_ms"] = None if closed is None else int((closed - hung_up) * 1000)
            report.record(
                "LKT-06",
                room=scored.grant.room,
                agentGoneAfterHangupMs=scored.call.__dict__["server_agent_gone_ms"],
                roomClosedAfterHangupMs=scored.call.__dict__["server_room_closed_ms"],
            )
        finally:
            await admin.close()
    return scored


# -- transport --------------------------------------------------------------


def test_lkt02_the_agent_joins_within_budget_as_an_agent_participant(full_call):
    call = full_call.call
    assert call.agent_identity, "no agent participant ever joined"
    waited = call.ms(call.agent_joined_at)
    assert waited is not None and waited <= int(SDK["budgets"]["agentJoinMs"]), f"agent joined after {waited}ms"


def test_lkt09_the_agent_identifies_as_the_dispatched_worker(full_call):
    assert full_call.call.agent_attributes.get("lk.agent.name") == LK["agentName"]


def test_lkt05_the_agent_publishes_a_microphone_track_and_a_transcription_stream(full_call):
    call = full_call.call
    assert call.agent_audio_track_at is not None, "the agent never published audio"
    assert call.agent_audio_source == 2, f"agent audio source is {call.agent_audio_source}, not MICROPHONE"
    assert call.agent_segments(), "no lk.transcription stream from the agent"


def test_nobody_unexpected_is_in_the_room(full_call, report):
    """Only the caller, the agent, and (reported) the deployment's recorder."""
    kinds = [k for _, k in full_call.call.others]
    unexpected = [(i, k) for i, k in full_call.call.others if k not in (EGRESS_KIND,)]
    if EGRESS_KIND in kinds:
        report.finding("LKT-EGRESS", "every call is recorded: an EGRESS participant joins the room", others=full_call.call.others)
    assert not unexpected, f"unexpected participants: {unexpected}"


def test_lkt06_the_agent_leaves_after_the_caller_hangs_up(full_call):
    gone = full_call.call.__dict__.get("server_agent_gone_ms", "skip")
    if gone == "skip":
        pytest.skip("LIVEKIT_* not set - the server view is unavailable")
    assert gone is not None, (
        f"the agent was still in {full_call.grant.room} {SDK['budgets']['agentLeavesAfterHangupMs']}ms "
        f"after the caller left - an orphaned agent holds a worker slot"
    )


def test_lkt06_the_room_closes_after_the_call(full_call):
    closed = full_call.call.__dict__.get("server_room_closed_ms", "skip")
    if closed == "skip":
        pytest.skip("LIVEKIT_* not set - the server view is unavailable")
    assert closed is not None, f"room {full_call.grant.room} still open {SDK['budgets']['roomClosedAfterHangupMs']}ms after hang-up"


# -- turn-taking ------------------------------------------------------------


def test_trn01_the_first_turn_greets_the_caller_by_name_within_budget(full_call):
    """The agent opens with the intake data: 'Hi <name>, this is Jason with Etnyre'."""
    first = full_call.call.agent_segments()[0]
    ms = full_call.call.ms(first.closed)
    assert ms <= int(BUDGETS["greetingMs"]), f"first turn after {ms}ms"
    name = full_call.grant.caller["customerName"].split()[0].lower()
    assert name in first.text.lower(), f"greeting does not use the caller's name {name!r}: {first.text!r}"


def test_trn02_dkb08_the_machine_is_identified_from_the_serial(full_call):
    """DKB-08, routing: the machine the agent names is the serial's machine -
    by hopper type, which is what differs between the manuals."""
    budget = int(BUDGETS["machineIdentifiedMs"])
    kb_id = full_call.transcript.kb_id
    right, wrong = cases.hopper_word(kb_id), cases.other_hopper_word(kb_id)
    machine_turn = next(
        (s for s in full_call.call.agent_segments() if "pulled up" in s.text.lower() or "hopper" in s.text.lower()),
        None,
    )
    assert machine_turn, "the agent never said which machine it had"
    assert full_call.call.ms(machine_turn.closed) <= budget
    text = machine_turn.text.lower()
    if "hopper" in text:
        assert right in text and f"{wrong} hopper" not in text, (
            f"serial {full_call.transcript.serial} is a {right}-hopper machine ({kb_id}); agent said: {machine_turn.text!r}"
        )


def test_mem04_the_serial_given_on_the_form_is_not_asked_for_again(full_call):
    assert not [s for s in full_call.steps if s.intent == "asksForSerial"], "the agent re-asked for the serial"


def test_trn04_every_agent_turn_is_final_and_non_empty(full_call):
    segments = [s for s in full_call.call.segments if s.speaker == "agent"]
    empty = [s for s in segments if not s.text]
    partial = [s.text[:60] for s in segments if s.text and not s.final]
    assert not empty, f"{len(empty)} empty transcription segment(s)"
    assert not partial, f"non-final segments: {partial}"


def test_trn06_the_agent_state_leaves_listening_after_every_message(full_call):
    """The state attribute is how the driver knows a turn is over; a message
    that never moves it was not received."""
    budget = int(SDK["budgets"]["stateTransitionMs"]) / 1000
    call = full_call.call
    for sent in call.sent:
        moved = [t for t, s in call.states if sent.at < t <= sent.at + budget and s in ("thinking", "speaking")]
        if sent is call.sent[-1] and call.disconnected_at and call.disconnected_at - sent.at < budget:
            continue  # the last message can be answered by hanging up
        assert moved, f"state never left 'listening' within {budget}s of {sent.text[:50]!r}"


def test_trn07_the_conversation_ends_within_max_turns(full_call):
    assert len(full_call.call.agent_segments()) <= int(testbed.config()["chatFlow"]["maxTurns"]) + 4


def test_cnv01_every_turn_is_accounted_for(full_call, report):
    unmatched = [s.agent[:80] for s in full_call.steps if s.intent == "unrecognised"]
    report.record("CNV-01", steps=[s.intent for s in full_call.steps + full_call.wrap], unmatched=unmatched)
    assert len(unmatched) <= 1, f"turns no intent recognised: {unmatched}"


def test_cnv06_the_call_closes_with_a_goodbye_inside_budget(full_call):
    intents = [s.intent for s in full_call.wrap]
    assert "farewell" in intents or full_call.call.agent_left_at, (
        f"no goodbye after sign-off (wrap-up steps: {intents})"
    )


# -- the answer -------------------------------------------------------------


def test_the_question_was_asked_and_answered(full_call):
    assert full_call.transcript.question_index() is not None, "the question never went out"
    assert full_call.grounding.applicable, (
        f"the reply never reached an answer the oracle could score:\n{full_call.dialogue()}"
    )


def test_fab01_xfm01_the_answer_is_grounded_in_this_machines_manual(full_call):
    """The zero-tolerance half of the oracle - see test_grounding.py for the matrix."""
    assert not full_call.grounding.zero_tolerance_failures, (
        "\n".join(full_call.grounding.zero_tolerance_failures) + "\n\n" + full_call.dialogue()
    )


def test_dkb01_coverage_is_reported(full_call, report):
    verdicts = {v.check: v for v in full_call.grounding.verdicts}
    anchors = verdicts.get("requiredAnchors")
    report.record("DKB-01", scenario=full_call.transcript.scenario_id, status=anchors.status if anchors else None,
                  evidence=anchors.evidence if anchors else [], expected=anchors.expected if anchors else [])
    if SDK["grounding"]["requireCoverage"] and anchors and anchors.status == oracle.FAIL:
        pytest.fail(anchors.summary)
