"""
The KB-steps validator, offline. Every transcript in fixtures/validator/cases.yaml
is checked against fixtures/validator/entry.yaml: the items listed under `expect`
must fail with exactly that result, and everything else must pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lkqa.validator import normalize, numbers_with_units, split_steps, validate

pytestmark = pytest.mark.offline

FIXTURES = Path(__file__).parent / "fixtures" / "validator"
ENTRY = yaml.safe_load((FIXTURES / "entry.yaml").read_text(encoding="utf-8"))
CASES = yaml.safe_load((FIXTURES / "cases.yaml").read_text(encoding="utf-8"))["cases"]

RULES = {"missing", "out_of_order", "merged", "missing_caution", "misplaced_caution", "wrong_value"}


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_transcript(case):
    result = validate(ENTRY, case["turns"])
    failed = {i.ref: i.result for i in result.items if not i.passed}
    assert failed == case["expect"], (
        f"{case['name']}\n{result.explain()}\nsegments:\n" +
        "\n".join(f"  [{s.index}] {s.text}" for s in result.segments)
    )
    assert result.passed is (not case["expect"])


def test_every_rule_has_a_passing_and_a_failing_fixture():
    for rule in RULES:
        mine = [c for c in CASES if c["rule"] == rule]
        assert any(not c["expect"] for c in mine), f"no passing fixture for {rule}"
        assert any(rule in c["expect"].values() for c in mine), f"no failing fixture for {rule}"
    assert any(c["rule"] == "reworded" and not c["expect"] for c in CASES)


def test_every_failure_has_a_plain_english_reason():
    for case in CASES:
        for item in validate(ENTRY, case["turns"]).items:
            if not item.passed:
                assert item.reason, f"{case['name']}: {item.ref} failed with no reason"


@pytest.mark.parametrize(
    ("spoken", "written"),
    [
        ("forty to sixty P S I", "40–60 PSI"),
        ("forty through sixty pounds per square inch", "40-60 psi"),
        ("thirty seconds", "30 seconds"),
        ("two thousand two hundred R P M", "2,200 RPM"),
        ("twenty two hundred RPM", "2200 rpm"),
        ("three hundred feet per minute", "300 FPM"),
        ("one sixteenth of an inch", '1/16"'),
        ("zero point nine amps", "0.900 amps"),
        ("five volts DC", "5.0 VDC"),
        ("four inches", "4.00 inches"),
        ("the Park/Drive switch", "the park drive switch"),
        ("“IDLE” position", '"idle" positions'),
    ],
)
def test_normalisation_makes_spoken_and_written_forms_equal(spoken, written):
    assert normalize(spoken) == normalize(written)


def test_numbers_are_read_with_their_units():
    assert numbers_with_units(normalize("crank for thirty seconds at forty to sixty PSI")) == [
        ("30", "second"), ("40 to 60", "psi")]


def test_split_uses_agent_markers_and_turns():
    segments, method = split_steps(["First, do A. Then do B.", "Step three: do C. Finally, do D."])
    assert method == "markers"
    assert [s.text for s in segments] == ["First, do A.", "Then do B.", "Step three: do C.", "Finally, do D."]
    assert [s.turn for s in segments] == [0, 0, 1, 1]


def test_split_falls_back_to_sentences_without_markers():
    segments, method = split_steps(["Do A. Do B.", "Do C."])
    assert method == "sentences"
    assert [s.text for s in segments] == ["Do A.", "Do B.", "Do C."]


def test_empty_answer_fails_every_item():
    result = validate(ENTRY, [])
    assert not result.passed
    assert all(not i.passed for i in result.items)
