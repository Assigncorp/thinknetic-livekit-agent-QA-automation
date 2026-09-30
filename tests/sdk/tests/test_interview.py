"""
INT: an adaptive interview on a live call - LLM-written questions, KB-only,
each one a follow-up to the agent's previous answer, each answer judged.

Per machine: one call (INTERVIEW_CALLS), an opening question from a random
passage of that machine's KB, then INTERVIEW_TURNS follow-ups, each written from
the passages that best match what the agent just said. A question is asked only
if its kb_quote is verbatim in the KB file (lkqa/interview.verify_quote).

Each answer gets two verdicts:
  * the deterministic oracle - every figure in this machine's manual, none from
    another machine's, and a value of the asked kind must be the KB's;
  * the LLM judge - the product owner's auditor rubric, claim by claim.
Any FAIL from either fails the test (agreed 2026-09-28). A judge FAIL whose
objections cannot be found in the answer is flagged evidenceVerified=false in
the report so a person checks it first.

Needs a free LLM key (lkqa/llm.py); skips with the reason otherwise.
Results: report/data/interview.json and report/interview.md, and in report/index.html.
"""

from __future__ import annotations

import os

import pytest

from lkqa import cases, interview, llm
from lkqa.bridge import testbed
from lkqa.call import AgentHungUp, Call
from lkqa.session import request_session

pytestmark = [pytest.mark.live, pytest.mark.interview]

SDK = testbed.config()["livekitSdk"]
CFG = SDK["interview"]


async def test_int01_llm_follow_up_questions_from_the_kb_get_kb_correct_answers(report, r):
    ok, why = llm.available()
    if not ok:
        pytest.skip(f"LLM unavailable: {why}")
    turns = int(os.getenv("INTERVIEW_TURNS", CFG["turns"]))
    per_machine = int(os.getenv("INTERVIEW_CALLS", CFG["callsPerMachine"]))
    budgets = testbed.config()["budgets"]
    calls: list[dict] = []

    try:
        for kb in cases.serial_routed_kbs():
            for _ in range(per_machine):
                serial = cases.serial_for(kb["id"], r)
                grant = request_session(cases.caller(r, serial))
                asked: list[interview.Asked] = []
                print(f"\n[int] {kb['id']} serial {serial} room {grant.room}")
                async with Call(grant) as call:
                    await call.settle(timeout_ms=int(budgets["machineIdentifiedMs"]), drain=True)
                    last = ""
                    for n in range(turns + 1):
                        if call.agent_gone:
                            break
                        try:
                            q = interview.next_question(kb["id"], last, asked, r)
                        except llm.LlmBadOutput as exc:
                            # The question WRITER failed, not the agent: end this
                            # call's interview and say so. No question = no verdict,
                            # and the `assert rows` below still fails an empty run.
                            print(f"[int]  no follow-up written: {exc}")
                            report.finding("INT-01", "the LLM could not write a KB-grounded follow-up",
                                           kb=kb["id"], turn=n + 1, reason=str(exc))
                            break
                        print(f"[int]  Q{n + 1} ({q.entry.id}): {q.question}")
                        try:
                            q.answer, _ = await call.ask(q.question)
                        except AgentHungUp as exc:
                            # The agent left mid-interview (VERIFIED 2026-09-30,
                            # no goodbye, after correct answers). A finding, not a
                            # crash: the answers already judged stand.
                            print(f"[int]  agent left the call: {exc}")
                            report.finding("INT-01", "the agent left the call mid-interview, without a goodbye",
                                           kb=kb["id"], turn=n + 1, room=grant.room)
                            break
                        q.oracle = interview.answer_figures_check(kb["id"], q)
                        q.judge = interview.judge(kb["id"], q) if q.answer.strip() else {"verdict": "INCONCLUSIVE", "objections": []}
                        q.verdict = interview.verdict_of(q)
                        print(f"[int]  A{n + 1}: {q.answer[:220]}")
                        print(f"[int]  -> {q.verdict}  oracle={q.oracle['failures'] or 'ok'}  judge={q.judge.get('verdict')} {q.judge.get('objections') or ''}")
                        asked.append(q)
                        last = q.answer
                    transcript = call.to_transcript({"id": f"INTERVIEW-{kb['id']}", "kbId": kb["id"],
                                                     "question": asked[0].question if asked else ""})
                path = report.save_transcript(transcript, f"interview-{kb['id']}")
                calls.append({"kb": kb["id"], "serial": serial, "room": grant.room, "recording": path.name,
                              "questions": [interview.as_dict(a) for a in asked]})
    finally:
        if calls:
            interview.write_report(calls)

    rows = [q for c in calls for q in c["questions"]]
    report.record("INT-01", calls=len(calls), questions=len(rows),
                  verdicts={k: sum(q["verdict"] == k for q in rows) for k in ("PASS", "FAIL", "INCONCLUSIVE", "NOT ANSWERED")})
    failed = [(c["kb"], q) for c in calls for q in c["questions"] if q["verdict"] == "FAIL"]
    assert rows, "no question was asked"
    assert not failed, "answers not correct per the KB (report/interview.md):\n  " + "\n  ".join(
        f"{kb}: {q['question']} -> {'; '.join(q['oracle'].get('failures') or [])} {'; '.join(q['judge'].get('objections') or [])}"
        + ("" if q["judge"].get("evidenceVerified", True) else " [judge evidence not found in the answer]")
        for kb, q in failed
    )
