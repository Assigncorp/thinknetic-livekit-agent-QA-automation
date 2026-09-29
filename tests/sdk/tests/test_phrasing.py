"""
PHR: positive corner cases - the same KB question, phrased the way callers type.

A real caller does not write "What is the main relief pressure for steering?".
They write it in lowercase with no question mark, in capitals, with typos, buried
in small talk, as three keywords, as a statement, with spoken hesitations, or
after a paragraph about their morning. Every one of those must still get the
KB's value.

Each variant is one live call (livekitSdk.phrasing) on an FAQ the agent answers
correctly when asked plainly, so a failure is the phrasing's doing. The verdict
is the KB run's, with no model: sectionValues must PASS - the direct answer
states the value THAT entry gives - and no zero-tolerance check may fail.
`make livekit-phrasing`; ~8 calls, one at a time.
"""

from __future__ import annotations

import re

import pytest

from lkqa import cases, phrasing
from lkqa.bridge import testbed
from lkqa.driver import scored_call
from lkqa.kbrun import row

CFG = testbed.config()["livekitSdk"]["phrasing"]
CASES = [(v, CFG["scenarios"][i % len(CFG["scenarios"])]) for i, v in enumerate(CFG["variants"])]
NUMBER_WORDS = re.compile(r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|\d+)\b", re.I)


# ---------------------------------------------------------------------------
# The rewrites themselves - no network
# ---------------------------------------------------------------------------


@pytest.mark.offline
@pytest.mark.parametrize("variant,scenario_id", CASES, ids=[f"{v}-{s}" for v, s in CASES])
def test_phr00_every_rewrite_changes_the_text_but_keeps_the_topic_and_adds_no_figure(variant, scenario_id):
    """A rewrite that left the question as it was would test nothing; one that
    dropped the topic would test the agent's guessing; one that added a figure
    would put a number in the call that the oracle might then attribute to
    the agent's knowledge."""
    question = testbed.scenario_by_id(scenario_id)["question"]
    out = phrasing.rewrite(variant, question)
    assert out != question
    topic = [w.lower() for w in re.findall(r"[A-Za-z]{5,}", phrasing.keywords(question))]
    hits = [w for w in topic if w in out.lower() or w[:4] in out.lower()]
    assert len(hits) >= max(1, len(topic) - 2), f"{variant} lost the topic: {out!r}"
    assert NUMBER_WORDS.findall(out) == NUMBER_WORDS.findall(question), f"{variant} added a figure: {out!r}"


@pytest.mark.offline
def test_phr00_rewrites_are_deterministic_and_every_configured_variant_exists():
    question = testbed.scenario_by_id(CFG["scenarios"][0])["question"]
    for variant in CFG["variants"]:
        assert phrasing.rewrite(variant, question) == phrasing.rewrite(variant, question)
    for scenario_id in CFG["scenarios"]:
        assert testbed.scenario_by_id(scenario_id)["kind"] == "faq", f"{scenario_id} is not an FAQ entry"


# ---------------------------------------------------------------------------
# Live - one call per variant
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.phrasing
@pytest.mark.parametrize("variant,scenario_id", CASES, ids=[f"{v}-{s}" for v, s in CASES])
async def test_phr01_the_kb_question_phrased_this_way_still_gets_the_kb_value(variant, scenario_id, report, r):
    scenario = testbed.scenario_by_id(scenario_id)
    question = phrasing.rewrite(variant, scenario["question"])
    serial = cases.serial_for(scenario["kbId"], r)
    scored = await scored_call(
        report, f"phrasing-{variant}", scenario, serial, r,
        question=question, section_scenario=scenario, mode="faq",
    )
    result = row(scenario, scored, serial, None)
    report.record("PHR-01", variant=variant, scenario=scenario_id, question=question,
                  expected=result.get("expected"), stated=result.get("stated"), verdict=result["verdict"])
    assert result["verdict"] == "PASS", (
        f"{variant}: {question!r}\n"
        f"expected {result.get('expected')}, the agent stated {result.get('stated') or 'no value of that kind'}"
        f" -> {result['verdict']} {result.get('failures') or ''}\n{scored.dialogue()}"
    )
