"""
The LiveKit KB-steps smoke call - one live call to the deployed agent.

Picks one model at random (seed logged; KB_SEED / KB_MODEL / KB_QUESTION_ID
reproduce or pin it), routes its smoke serial through the workbook, asks one
question from that model's KB, and validates the answer step by step. A failed
call is retried once in a fresh room; both attempts land in the report.

Results: report/data/kb-smoke.json -> tools/build_report.py -> report/index.html.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone

import pytest

from lkqa.bank import choose
from lkqa.call import missing_credentials
from lkqa.expect import RunResult
from lkqa.kbcall import FEEDBACK_ASK, run_attempt
from lkqa.routing import ROOT

pytestmark = pytest.mark.live

RESULT = ROOT / "report" / "data" / "kb-smoke.json"
RETRIES = int(os.getenv("KB_RETRIES", "1"))


async def test_kb_steps_call(product, caller):
    if missing := missing_credentials():
        pytest.skip(f"{', '.join(missing)} not set in .env")

    started = datetime.now(timezone.utc)
    selection = choose()
    print(f"\n[kb] seed={selection.seed} (KB_SEED={selection.seed} reproduces this run) "
          f"model={selection.model} serial={selection.serial} question={selection.entry['id']}")
    rng = random.Random(selection.seed)

    attempts = []
    for number in range(1, RETRIES + 2):
        attempt = await run_attempt(number, selection.entry, selection.serial, selection.model,
                                    product, caller, rng)
        attempts.append(attempt)
        if attempt.passed:
            break
        if number <= RETRIES:
            print(f"[kb] attempt {number} failed - retrying once in a fresh room")
    final = attempts[-1]

    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps({
        "startedAt": started.isoformat(),
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "passed": final.passed,
        "retried": len(attempts) > 1,
        "selection": selection.as_dict(),
        "entry": selection.entry,
        "attempts": [a.as_dict() for a in attempts],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[kb] result -> {RESULT.relative_to(ROOT)}")

    # LiveKit-style assertions over the final attempt's recorded events.
    failed = [f"{c.name}: {c.detail}" for c in final.checkpoints.values() if not c.passed]
    if final.error:
        failed.append(f"error: {final.error}")
    run = RunResult(final.events)
    if final.checkpoints["greeted"].passed:
        run.expect.next_event().is_message(role="assistant")
    if final.checkpoints["feedback_asked"].passed:
        run.expect.contains_message(role="assistant", matching=FEEDBACK_ASK, what="rating request")
    if final.validation and not final.validation.passed:
        failed += [f"  {i.ref}: {i.reason}" for i in final.validation.failures]
    rooms = "; ".join(f"attempt {a.number}: room {a.room} (sid {a.room_sid or '-'})" for a in attempts)
    assert not failed, (
        f"KB-steps call failed ({len(attempts)} attempt(s); KB_SEED={selection.seed}; {rooms}):\n  "
        + "\n  ".join(failed))
