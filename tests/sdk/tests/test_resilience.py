"""
RES / TRN-05 / MEM: the call when the caller does not follow the script.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from conftest import gate
from lkqa import cases, grounding
from lkqa.bridge import oracle, testbed
from lkqa.call import AgentHungUp, Call
from lkqa.driver import scored_call, timings
from lkqa.session import request_session

pytestmark = pytest.mark.live

SDK = testbed.config()["livekitSdk"]
BUDGETS = testbed.config()["budgets"]


async def test_res09_an_unknown_serial_yields_no_machine_specific_figure(report, r):
    """RES-09. A serial in no workbook: the agent has no machine, so the only
    figures it may give are ones every machine shares (the general guide)."""
    kb = cases.serial_routed_kbs()[0]
    question = testbed.scenario_by_id(testbed.config()["livekitSdk"]["traps"]["falsePremise"]["scenarioId"])["question"]
    adhoc = {"id": "UNKNOWN-SERIAL", "kbId": "", "question": question}
    scored = await scored_call(report, "unknown-serial", adhoc, SDK["unknownSerial"], r)
    machine = [s.text for s in scored.call.agent_segments() if "pulled up" in s.text.lower()]
    answer = scored.transcript.full_answer
    found, foreign = grounding.general_only(answer)
    report.record("RES-09", machineClaims=machine, figures=found, machineSpecific=foreign)
    assert not foreign, (
        f"serial {SDK['unknownSerial']} routes to no manual, yet the agent gave machine-specific figures {foreign}:\n"
        + scored.dialogue()
    )
    hopper_claims = [t for t in machine if "hopper" in t.lower()]
    assert not hopper_claims, f"the agent claimed to have a machine for an unknown serial: {hopper_claims}"


async def test_trn05_a_message_sent_while_the_agent_is_speaking(report, r):
    """TRN-05. docs/chat-flow.md behaviour 3: a message sent mid-turn is dropped.
    This measures whether it still is. Report-only (gates.midStreamMessage)."""
    kb, scenario = cases.draw(r, SDK["grounding"]["kinds"], index=1)
    grant = request_session(cases.caller(r, cases.serial_for(kb["id"], r)))
    async with Call(grant) as call:
        speaking = await call.wait_for_state({"speaking"}, int(BUDGETS["greetingMs"]))
        assert speaking, "the agent never started its greeting"
        await asyncio.sleep(1.0)
        await call.say(scenario["question"], wait=False)
        sent_at = call.sent[-1].at
        answered = False
        deadline = time.monotonic() + (int(BUDGETS["answerMs"]) * 2) / 1000
        while time.monotonic() < deadline:
            turn = await call.next_agent_turn(int(BUDGETS["answerMs"]))
            if turn is None:
                break
            cited, _ = oracle.cited_anchors(turn.text, scenario["expectAnchors"])
            if cited:
                answered = True
                break
    report.record("TRN-05", scenario=scenario["id"], answeredMidStreamMessage=answered,
                  sentAtMs=call.ms(sent_at), turns=[s.text[:80] for s in call.agent_segments()])
    if not answered:
        if gate("midStreamMessage"):
            pytest.fail("a message sent while the agent was speaking was never answered")
        report.finding("TRN-05", "a question typed while the agent was speaking was not answered (dropped mid-stream)")


@pytest.mark.slow
async def test_res01_a_silent_caller_is_nudged_then_released(report, r):
    """RES-01. Say nothing after the greeting. Expect 'are you still there?'
    inside idlePromptMs, then the agent to end the call cleanly."""
    kb = cases.serial_routed_kbs()[2 % len(cases.serial_routed_kbs())]
    grant = request_session(cases.caller(r, cases.serial_for(kb["id"], r)))
    budget = int(SDK["budgets"]["idlePromptMs"])
    async with Call(grant) as call:
        await call.settle(timeout_ms=int(BUDGETS["machineIdentifiedMs"]), drain=True)
        quiet_from = time.monotonic()
        nudge = None
        while time.monotonic() - quiet_from < budget / 1000:
            turn = await call.next_agent_turn(budget)
            if turn is None:
                break
            if turn.idle:
                nudge = turn
                break
        left_at = None
        if nudge is not None:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline and not call.agent_gone:
                await asyncio.sleep(1)
            left_at = call.agent_left_at or call.disconnected_at
    report.record(
        "RES-01",
        nudgeAfterSilenceMs=None if nudge is None else int((nudge.closed - quiet_from) * 1000),
        nudgeText=None if nudge is None else nudge.text,
        agentEndedCallAfterSilenceMs=None if left_at is None else int((left_at - quiet_from) * 1000),
        timings=timings(call),
    )
    assert nudge is not None, f"no idle prompt within {budget}ms of silence (turns: {[s.text[:60] for s in call.agent_segments()]})"
    if left_at is None:
        report.finding("RES-01", "the agent nudged a silent caller but did not end the call within 120s")


@pytest.mark.slow
async def test_mem01_mem02_a_returning_caller_gets_a_recap_grounded_in_the_last_call(report, r):
    """MEM-01/02. Same caller, same serial, twice. The second greeting's recap
    may only contain figures from the manual or the previous call."""
    kb, scenario = cases.draw(r, SDK["grounding"]["kinds"], index=2)
    serial = cases.serial_for(kb["id"], r)
    person = cases.caller(r, serial)
    first = await scored_call(report, "memory-1", scenario, serial, r, caller=person)

    grant = request_session(person)
    async with Call(grant) as call:
        await call.settle(timeout_ms=int(BUDGETS["machineIdentifiedMs"]), drain=True)
    opening = " ".join(s.text for s in call.agent_segments())
    prior = first.transcript.full_answer
    found, _ = grounding.general_only(opening)
    allowed = oracle.allowed_measurements(kb["id"])
    from src import numerals

    prior_keys = {numerals.key_of(m) for m in numerals.extract(prior)}
    invented = [m.raw for m in numerals.extract(opening) if numerals.key_of(m) not in allowed | prior_keys]
    recalls = any(w in opening.lower() for w in ("last time", "previous", "left off", "before", "again"))
    topic = [w for w in scenario["question"].lower().split() if len(w) > 4 and w in opening.lower()]
    report.record("MEM-01", opening=opening, recallsPreviousCall=recalls, topicWords=topic, figures=found, invented=invented)
    assert not invented, f"the recap introduced figures in neither the manual nor the last call: {invented}"
    if not recalls:
        if gate("sessionMemory"):
            pytest.fail(f"a returning caller got no recap: {opening!r}")
        report.finding("MEM-01", "a returning caller (same name + serial) was not greeted with a recap")
