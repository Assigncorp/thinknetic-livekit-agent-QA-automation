"""
Offline validation of everything the judge depends on.

No network, no API account, no LiveKit. This is the file that runs on every PR,
and it is deliberately the largest one here, because almost every way an LLM
judge goes wrong is silent. A rubric the model never scores, a KB section that
resolves to the wrong lines, an anchor pattern that stopped matching - none of
those raise. They just produce numbers that look fine and mean nothing.

Same idea as api/tests/test_scenario_catalog.py: check the data the expensive
suites are about to rely on, before spending money finding out it was wrong.
"""

from __future__ import annotations

import pytest

from src import anchors, corpus, scorer, testbed
from src.transcript import load_recordings

pytestmark = pytest.mark.offline


# --------------------------------------------------------------------------
# The rubric set itself
# --------------------------------------------------------------------------


def test_rubrics_are_declared():
    rubrics = testbed.rubrics()
    assert rubrics, "judge.rubrics is empty - there is nothing to score"


def test_rubric_ids_are_unique():
    ids = [r["id"] for r in testbed.rubrics()]
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates, (
        f"duplicate rubric ids: {sorted(duplicates)}. The judge returns one entry "
        f"per id, so a duplicate silently drops one of them from the weighted mean"
    )


@pytest.mark.parametrize("rubric", testbed.rubrics(), ids=lambda r: r["id"])
def test_rubric_is_well_formed(rubric):
    assert 0.0 <= rubric["threshold"] <= 1.0, (
        f"{rubric['id']} has threshold {rubric['threshold']}, outside the 0-1 scale "
        f"the judge scores on"
    )
    assert int(rubric["weight"]) > 0, f"{rubric['id']} has non-positive weight"
    assert len(rubric["description"]) > 60, (
        f"{rubric['id']}'s description is {len(rubric['description'])} characters. It "
        f"goes into the judge's system prompt verbatim and is the ONLY instruction it "
        f"gets for this rubric - a terse one is answered with a guess"
    )


def test_a_rubric_that_gates_says_why():
    """A gating rubric can fail a release. The config has to carry the reason,
    because the person it fails will not have been in this conversation."""
    for rubric in testbed.rubrics():
        if rubric.get("gate"):
            assert rubric.get("_gateNote"), (
                f"{rubric['id']} is marked gate:true with no _gateNote. Every other "
                f"switch in this config that can fail a run explains itself"
            )


def test_gating_is_off_until_there_are_baselines():
    """
    Both gates ship off, and this test is here to make turning one on a
    deliberate act rather than a passing thought.

    docs/architecture.md: semantic scoring is reported separately so a
    borderline score never blocks a release. The thresholds are currently
    guesses - read off the KBs, not measured from calls - and a gate on a
    guessed threshold is how a suite gets muted. Delete this test when you
    turn a gate on, and say in the commit what baseline justified it.
    """
    cfg = testbed.judge_config()
    assert cfg["requireScoreGate"] is False
    assert cfg["requireSafetyGate"] is False


# --------------------------------------------------------------------------
# KB grounding - the part that decides whether a score means anything
# --------------------------------------------------------------------------


def test_every_scenario_resolves_to_a_kb_section():
    """
    A scenario whose section cannot be found would be judged against whatever
    the fallback window happened to catch, and the resulting score would be
    confident nonsense. 221 scenarios, so this is the cheap way to know.
    """
    failures = []
    for scenario in testbed.all_scenarios():
        try:
            section = corpus.section_for(scenario)
        except Exception as exc:  # noqa: BLE001 - reporting every failure at once
            failures.append(f"{scenario['id']}: {type(exc).__name__}: {exc}")
            continue
        if not section.text.strip():
            failures.append(f"{scenario['id']}: resolved to an empty section")

    assert not failures, "scenarios that do not resolve to KB text:\n" + "\n".join(failures)


def test_grounding_context_stays_inside_its_budget():
    limit = int(testbed.judge_config()["contextSectionChars"])
    oversized = []
    for scenario in testbed.all_scenarios():
        section = corpus.section_for(scenario)
        # The clamp adds a short "[... omitted ...]" marker, hence the slack.
        if len(section.text) > limit + 200:
            oversized.append(f"{scenario['id']}: {len(section.text)} chars")

    assert not oversized, (
        f"sections over judge.contextSectionChars ({limit}):\n" + "\n".join(oversized)
    )


def test_the_section_actually_contains_the_question_it_was_chosen_for():
    """
    The single most likely way this layer goes quietly wrong: the right-looking
    section, from the wrong place in the file. Every score after that is
    confidently meaningless and nothing raises.

    Checked on the how-to scenarios, whose question is a `### Q:` heading and
    therefore appears verbatim in its own section.
    """
    misses = []
    for scenario in testbed.all_scenarios():
        if scenario.get("kind") != "howto":
            continue
        section = corpus.section_for(scenario)
        question = scenario["question"].strip()
        if question and question.lower() not in section.text.lower():
            misses.append(f"{scenario['id']}: {question[:60]!r} not in {section.citation()}")

    assert not misses, (
        f"{len(misses)} how-to scenario(s) were grounded on a section that does not "
        f"contain their own question:\n" + "\n".join(misses[:10])
    )


def test_controller_families_are_known_and_distinct():
    for kb in testbed.knowledge_bases(serial_routed_only=True):
        others = corpus.other_controller_families(kb["id"])
        assert others, (
            f"{kb['id']} has no opposing controller family, so the controllerFamily "
            f"rubric has nothing to catch it crossing into"
        )
        assert kb["controller"] not in others


def test_the_general_kb_is_family_neutral():
    """troubleshooting-general.md applies to any machine. Scoring it against a
    controller family would fail every answer that correctly stays generic."""
    assert corpus.other_controller_families("general") == []


# --------------------------------------------------------------------------
# Anchor matching - kept in step with the browser suite
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "anchor", "expected"),
    [
        # Written form.
        ("charge pressure should read 400 PSI", "400 PSI", True),
        ("install a 1000 PSI gauge in port G", "1000 PSI", True),
        # Spoken form - the agent is voice-first and writes the way it talks.
        ("should read approximately four hundred PSI", "400 PSI", True),
        ("one thousand pounds per square inch", "1000 PSI", True),
        ("tops out at four hundred feet per minute", "400 FPM", True),
        ("twenty five hundred feet per minute", "2,500 FPM", True),
        ("two thousand five hundred feet per minute", "2,500 FPM", True),
        ("you should read twelve volts", "12 VDC", True),
        ("coolant reaches two hundred forty degrees", "240°F", True),
        ("ninety six revolutions per minute", "96 RPM", True),
        # Loose separators.
        ("runs at four-hundred  feet per minute", "400 FPM", True),
        # Non-measurement anchors.
        ("check P1-PIN 21 on the harness", "P1-PIN 21", True),
        ("the filter is part 6703670", "6703670", True),
        # Must not match.
        ("nothing relevant here", "1000 PSI", False),
    ],
)
def test_anchor_matching(text, anchor, expected):
    assert anchors.cites_anchor(text, anchor) is expected


@pytest.mark.parametrize(
    ("text", "anchor"),
    [
        ("charge pressure should read 400 PSI", "0 PSI"),
        ("the reading was 10.00 amps", "0.00 amps"),
        ("you should see 1400 PSI", "400 PSI"),
        ("reads 12 VDC at the pin", "2 VDC"),
    ],
)
def test_an_anchor_does_not_match_inside_a_longer_number(text, anchor):
    """
    Regression. `0 PSI`, `0 VDC` and `0.00 amps` are real anchors - they are how
    these KBs write "you should read nothing here" - and as bare substrings they
    fire inside `400 PSI`. An answer citing the charge pressure was credited
    with citing the zero reading too, so anchorCoverage scored 3/3 on an answer
    that covered 2. Fixed in both this matcher and ui/src/utils/anchors.ts; if
    you change one, change both.
    """
    assert not anchors.cites_anchor(text, anchor), (
        f"{anchor!r} matched inside {text!r} - the boundary guard has regressed"
    )


def test_every_declared_anchor_can_match_itself():
    """An anchor that cannot match its own literal text can never be cited, so
    the scenario carrying it scores 0 on anchorCoverage forever."""
    broken = []
    for scenario in testbed.all_scenarios():
        for anchor in scenario.get("expectAnchors") or []:
            if not anchors.cites_anchor(f"the value is {anchor} here", anchor):
                broken.append(f"{scenario['id']}: {anchor!r}")

    assert not broken, "anchors that cannot match themselves:\n" + "\n".join(broken)


# --------------------------------------------------------------------------
# The prompt the judge is actually shown
# --------------------------------------------------------------------------


def test_the_prompt_carries_the_right_section_and_constraints():
    calls = load_recordings()
    if not calls:
        pytest.skip("no recordings to build a prompt from")

    call = calls[0]
    system, user = scorer.build_prompt(call)
    section = corpus.section_for(call.scenario())

    assert section.citation() in user, "the prompt does not say which KB text it quoted"
    assert call.question in user
    assert call.full_answer[:80] in user

    for rubric in testbed.rubrics():
        assert f"`{rubric['id']}`" in system, (
            f"{rubric['id']} is declared in config but never reaches the judge's "
            f"system prompt, so it is silently never scored"
        )


def test_the_prompt_forbids_the_judge_using_its_own_knowledge():
    """The one instruction this whole layer rests on. Without it the judge
    grades against its training data, which holds no Etnyre manual, and the
    suite becomes a test of the judge rather than of the deployment."""
    system, _ = scorer.build_prompt(
        load_recordings()[0]
    ) if load_recordings() else ("", "")
    if not system:
        pytest.skip("no recordings to build a prompt from")
    lowered = system.lower()
    assert "only source of truth" in lowered
    assert "your own knowledge" in lowered


def test_the_prompt_tells_the_judge_which_family_is_wrong():
    calls = [c for c in load_recordings() if c.controller]
    if not calls:
        pytest.skip("no family-specific recordings")
    _, user = scorer.build_prompt(calls[0])
    others = corpus.other_controller_families(calls[0].kb_id)
    for family in others:
        assert family in user, (
            f"the prompt never names {family} as the family this answer must not "
            f"drift into, so controllerFamily is being scored on vibes"
        )


# --------------------------------------------------------------------------
# Recordings
# --------------------------------------------------------------------------


def test_recordings_are_well_formed():
    for call in load_recordings():
        testbed.scenario_by_id(call.scenario_id)  # raises if unknown
        assert call.turns, f"{call.source} has no turns"
        assert call.question_index() is not None, (
            f"{call.source}: the caller never asks {call.question!r}, so there is no "
            f"answer to score - full_answer would fall back to the whole call"
        )
        for turn in call.turns:
            assert turn.speaker in {"agent", "caller"}, (
                f"{call.source}: unknown speaker {turn.speaker!r}"
            )


def test_synthetic_recordings_are_labelled_as_such():
    """
    A hand-written transcript scored as though it were a real call is the
    hollow-green failure this repo keeps designing against. Any fixture that is
    not a real call says so in the file, and the agreement test reads that label
    rather than inferring quality from the filename.
    """
    import json
    from pathlib import Path

    for path in sorted((Path(__file__).resolve().parents[1] / "recordings").glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if "_synthetic" in raw:
            assert raw.get("_expect") in {"high", "low"}, (
                f"{path.name} is synthetic but declares no _expect, so the agreement "
                f"test cannot use it"
            )
            assert len(raw["_synthetic"]) > 80, (
                f"{path.name} does not say what it is for"
            )
