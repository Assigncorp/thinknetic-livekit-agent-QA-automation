"""The answer check: keyword matching, offline."""

from __future__ import annotations

import pytest

from lkqa import smoke
from lkqa.validator import Keyword, normalize, validate

pytestmark = pytest.mark.offline

STARTUP = ["park", "neutral", "idle"]

# Each model's first start-up steps, worded the way its manual puts them. Whichever serial a call
# uses, an answer like these must pass on the keywords in kb/smoke.yaml.
MANUALS = {
    "VHRS28": ["Verify Park/Drive switch (item 2 on panel) is in the **PARK** position.",
               "Verify the Speed/Direction joystick (item 9) is in the **neutral** position.",
               "Turn the Throttle Run/Idle switch (item 37) to the **IDLE** position."],
    "FHRC28": ["Place the **Park/Drive switch** in the **Park** position.",
               "Verify the **control joystick** is in the **neutral** (center) position.",
               "Place the **Throttle Run/Idle switch** in the **Idle** position."],
    "VHRS36": ["Place **Park/Drive switch** in **PARK** position.",
               "Place **joystick** in **NEUTRAL** position.",
               "Place **Throttle Run/Idle switch** in **IDLE** position."],
    "FHRC36": ["Set Throttle: Place the Throttle Run/Idle switch (Ref 32) in the **IDLE** position.",
               "Set Mode: Confirm Park/Drive switch (Ref 2) is in **PARK**.",
               "Confirm Joystick Neutral: Verify the Speed/Direction Control Handle (Ref 9) is in neutral."],
}


@pytest.mark.parametrize("model", MANUALS)
def test_each_models_wording_passes_the_committed_keywords(model):
    v = validate(smoke.load().keywords, MANUALS[model])
    assert v.passed, v.explain()


def test_spoken_one_step_per_turn_passes():
    turns = ["Sure. First, make sure the park drive switch is set to park. Let me know when that's done.",
             "Next, check the joystick is centred in neutral.",
             "Then put the throttle switch on idle."]
    v = validate(STARTUP, turns)
    assert v.passed
    assert [i.turn for i in v.items] == [0, 1, 2]
    assert v.items[0].said == "First, make sure the park drive switch is set to park."


def test_order_does_not_matter():
    assert validate(STARTUP, ["Throttle to idle, joystick in neutral, and the switch in park."]).passed


def test_a_missing_keyword_fails_and_is_named():
    v = validate(STARTUP, ["Put the switch in park.", "Set the throttle to idle."])
    assert not v.passed
    assert [i.term for i in v.failures] == ["neutral"]
    assert v.score == pytest.approx(2 / 3)
    assert "NOT SAID] neutral" in v.explain()


def test_keywords_match_whole_words_only():
    assert not validate(["park"], ["Set the parking brake."]).passed
    assert not validate(["idle"], ["It sat idling."]).passed


def test_plurals_count_as_the_keyword():
    assert validate(["idle"], ["The engine idles for a minute."]).passed


def test_case_punctuation_and_markdown_are_ignored():
    assert validate(["idle"], ["**IDLE**"]).passed
    assert validate(["park"], ["the Park/Drive switch"]).passed


def test_a_synonym_counts_for_its_keyword():
    kw = Keyword.parse({"term": "neutral", "synonyms": ["center position"]})
    v = validate([kw], ["Keep the joystick in the center position."])
    assert v.passed and v.items[0].said_as == "center position"


def test_a_phrase_keyword_needs_its_words_together():
    assert validate(["walk-around check"], ["Did you do your walk around checks?"]).passed
    assert not validate(["walk-around check"], ["Walk to the cab and check the gauges."]).passed


def test_a_texted_list_is_read_line_by_line():
    text = "Startup steps:\n1. Park/Drive switch to PARK\n2. Joystick in NEUTRAL\n3. Throttle to IDLE"
    v = validate(STARTUP, [text])
    assert v.passed
    assert v.items[1].said == "2. Joystick in NEUTRAL"


def test_empty_answer_fails_every_keyword():
    v = validate(STARTUP, [])
    assert not v.passed and len(v.failures) == 3


def test_no_keywords_never_passes():
    assert not validate([], ["anything"]).passed


@pytest.mark.parametrize("raw", [True, None, "", "  ", {"term": "idle", "synonyms": [False]}, {"synonyms": ["x"]}])
def test_a_bad_keyword_is_refused(raw):
    with pytest.raises(ValueError):
        Keyword.parse(raw)


def test_as_dict_carries_what_the_report_shows():
    d = validate(STARTUP, ["Switch to park."]).as_dict()
    assert d["passed"] is False and d["score"] == pytest.approx(0.3333)
    assert d["items"][0] == {"term": "park", "synonyms": [], "passed": True, "saidAs": "park",
                             "said": "Switch to park.", "turn": 0}
    assert d["items"][1]["passed"] is False and d["items"][1]["said"] == ""


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


def test_a_value_keyword_matches_however_it_is_spoken():
    assert validate(["40-60 PSI"], ["Crank until you see forty to sixty P S I."]).passed
