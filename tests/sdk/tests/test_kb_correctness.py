"""
KB-RUN: many live calls, each judged against the knowledge-base files.

Is every value the agent gives the value resources/kb/*.md gives for that
question? Every anchored FAQ entry in every machine's KB is asked on a real call
over the LiveKit SDK, plus one procedure per machine and general-guide problems.
Each answer goes through the same zero-tolerance checks as test_grounding.py -
now including sectionValues, which fails a real-but-wrong figure (a value from
another page of the same manual) - with no model in the loop.

One test, many calls, `livekitSdk.kbRun.parallel` in flight at a time, so the
result is ONE table: report/kb-correctness.md (and .json). A failure lists
every wrong call with its evidence and KB citation, not just the first.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any

import pytest

from lkqa import cases
from lkqa.bridge import testbed
from lkqa.driver import scored_call
from lkqa.kbrun import plan, row, write

pytestmark = [pytest.mark.live, pytest.mark.kbrun]

RUN = testbed.config()["livekitSdk"]["kbRun"]


async def test_kb_every_value_the_agent_gives_matches_the_knowledge_base(report, r):
    scenarios, excluded = plan()
    assert scenarios, "nothing to call - run `make resources`"
    machine_kbs = [kb["id"] for kb in cases.serial_routed_kbs()]
    # KB_PARALLEL overrides the config: `make live-parallel` runs 8 at a time.
    sem = asyncio.Semaphore(int(os.getenv("KB_PARALLEL") or RUN["parallel"]))
    rows: list[dict[str, Any]] = []

    # Serials rotate through each KB's pool without repeats, because the agent
    # remembers callers per serial.
    pools = {kb: random.Random(i).sample(testbed.serials_for(kb), len(testbed.serials_for(kb))) for i, kb in enumerate(machine_kbs)}
    turn = {kb: 0 for kb in machine_kbs}

    def next_serial(kb_id: str) -> str:
        pool = pools[kb_id]
        s = pool[turn[kb_id] % len(pool)]["serial"]
        turn[kb_id] += 1
        return s

    async def one(i: int, scenario: dict[str, Any]) -> None:
        general = scenario["kbId"] not in machine_kbs
        call_kb = machine_kbs[i % len(machine_kbs)] if general else scenario["kbId"]
        serial = next_serial(call_kb)
        async with sem:
            try:
                scored = await scored_call(
                    report, f"kb-{scenario['id']}", {**scenario, "kbId": call_kb}, serial, r,
                    section_scenario=scenario,
                    mode="faq" if scenario.get("kind") == "faq" else "default",
                )
                rows.append(row(scenario, scored, serial, None))
            except Exception as exc:  # noqa: BLE001 - one broken call must not hide the other 47
                rows.append(row(scenario, None, serial, f"{type(exc).__name__}: {exc}"))

    await asyncio.gather(*(one(i, s) for i, s in enumerate(scenarios)))
    write(rows, excluded)
    report.record("KB-RUN", calls=len(rows), excluded=excluded,
                  verdicts={k: sum(x["verdict"] == k for x in rows) for k in ("PASS", "FAIL", "NOT SCORED", "ERROR")})

    wrong = [x for x in rows if x["verdict"] in ("FAIL", "ERROR")]
    print(f"\n[kb] {len(rows)} calls -> report/kb-correctness.md")
    assert not wrong, "calls where the agent's values do not match the KB (or the call broke):\n  " + "\n  ".join(
        f"{x['scenario']} ({x['kb']}): {x.get('failures') or x.get('error')}" for x in wrong
    )
