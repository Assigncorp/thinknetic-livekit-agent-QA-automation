"""
LKT-07 / MEM-05: several callers at once, each with a different machine.

Three calls in parallel - the number approved for the shared dev deployment -
each on a different knowledge base, all asking the SAME question. Each must get
its own agent, its own machine, and its own manual's answer. Cross-talk between
sessions shows up here as a foreign figure (crossFamilyForbidden) or a machine
named for the wrong serial. Not a load test.
"""

from __future__ import annotations

import asyncio

import pytest

from lkqa import cases
from lkqa.bridge import testbed
from lkqa.driver import scored_call

pytestmark = [pytest.mark.live, pytest.mark.concurrency]

SDK = testbed.config()["livekitSdk"]


async def test_lkt07_parallel_callers_get_their_own_agent_machine_and_manual(report, r):
    scenarios = cases.shared_question_across_kbs(int(SDK["concurrency"]["calls"]))
    assert scenarios, "no question is shared by enough machines (see test_offline)"
    calls = await asyncio.gather(
        *[
            scored_call(report, f"concurrent-{i}-{s['kbId']}", s, cases.serial_for(s["kbId"], r), r)
            for i, s in enumerate(scenarios)
        ]
    )

    agents = [c.call.agent_identity for c in calls]
    rooms = [c.grant.room for c in calls]
    report.record("LKT-07", rooms=rooms, agents=agents, kbs=[s["kbId"] for s in scenarios])
    assert all(agents), "a parallel caller got no agent"
    assert len(set(agents)) == len(agents), f"one agent served two rooms: {agents}"
    assert len(set(rooms)) == len(rooms)

    problems = []
    for c, s in zip(calls, scenarios):
        if c.grounding.zero_tolerance_failures:
            problems.append(f"{s['kbId']}: {c.grounding.zero_tolerance_failures}")
        machine = " ".join(t.text.lower() for t in c.call.agent_segments() if "hopper" in t.text.lower())
        if machine and f"{cases.other_hopper_word(s['kbId'])} hopper" in machine:
            problems.append(f"{s['kbId']}: named the wrong hopper type: {machine[:120]}")
    assert not problems, "cross-talk between parallel sessions:\n  " + "\n  ".join(problems)
