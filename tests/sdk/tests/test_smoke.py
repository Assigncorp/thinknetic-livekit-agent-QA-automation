"""kb/smoke.yaml - the four serials, the question, its keywords and the image - and how a run picks from it. Offline."""

from __future__ import annotations

import pytest

from lkqa import smoke

pytestmark = pytest.mark.offline


@pytest.fixture(autouse=True)
def no_pins(monkeypatch):
    for name in ("KB_SEED", "KB_MODEL"):
        monkeypatch.delenv(name, raising=False)


def write(tmp_path, body: str):
    path = tmp_path / "smoke.yaml"
    path.write_text(body, encoding="utf-8")
    return path


SERIALS = "serials:\n  FHRC28: K7174\n  FHRC36: K6758\n  VHRS28: K7170\n  VHRS36: K6757\n"
IMAGE = "image: Operator controls\n"
REST = "question: How do I start it?\nkeywords: [park, neutral, idle]\n" + IMAGE


def test_the_committed_file_is_valid():
    config = smoke.load()
    assert set(config.serials) == set(smoke.MODELS)
    assert len(set(config.serials.values())) == 4
    assert config.question.strip()
    assert config.keywords
    assert config.image


def test_a_minimal_file_loads(tmp_path):
    config = smoke.load(write(tmp_path, SERIALS + REST))
    assert config.serials == {"FHRC28": "K7174", "FHRC36": "K6758", "VHRS28": "K7170", "VHRS36": "K6757"}
    assert config.question == "How do I start it?"
    assert [k.term for k in config.keywords] == ["park", "neutral", "idle"]
    assert config.image == "Operator controls"


def test_model_names_and_serials_are_normalised(tmp_path):
    body = SERIALS.replace("FHRC28: K7174", "fhrc28: ' k7174 '") + REST
    assert smoke.load(write(tmp_path, body)).serials["FHRC28"] == "K7174"


def test_keywords_can_carry_synonyms(tmp_path):
    body = SERIALS + IMAGE + "question: Q?\nkeywords:\n  - park\n  - term: neutral\n    synonyms: [center position]\n"
    kw = smoke.load(write(tmp_path, body)).keywords[1]
    assert (kw.term, kw.synonyms) == ("neutral", ("center position",))


@pytest.mark.parametrize(("body", "message"), [
    (SERIALS.replace("  VHRS36: K6757\n", "") + REST, "no serial for VHRS36"),
    (SERIALS.replace("FHRC28", "FHRC26") + REST, "FHRC26 is not a model name"),
    (SERIALS.replace("K6758", "") + REST, "FHRC36 needs one serial"),
    (SERIALS.replace("K6758", "[K6758, K6759]") + REST, "FHRC36 needs one serial"),
    (SERIALS.replace("K6758", "K7174") + REST, "K7174 is given for both FHRC28 and FHRC36"),
    (SERIALS + IMAGE + "keywords: [park]\n", "'question' is empty"),
    (SERIALS + IMAGE + "question: Q?\nkeywords: []\n", "'keywords' must list at least one keyword"),
    (SERIALS + IMAGE + "question: Q?\n", "'keywords' must list at least one keyword"),
    (SERIALS + IMAGE + "question: Q?\nkeywords: [park, on]\n", "YAML read a keyword as True; quote it"),
    (SERIALS + IMAGE + "question: Q?\nkeywords: [park, PARK]\n", "'PARK' is listed twice"),
    (SERIALS + REST.replace(IMAGE, ""), "'image' must give the description of one knowledge-base image"),
    (SERIALS + REST.replace(IMAGE, "image: ''\n"), "'image' must give the description"),
    (SERIALS + REST.replace(IMAGE, "image: [Air oiler, Air system]\n"), "'image' must give the description"),
    ("serials: [K7174]\n" + REST, "'serials' must give one serial under each model name"),
])
def test_a_bad_file_fails_before_any_call(tmp_path, body, message):
    with pytest.raises(smoke.ConfigError, match=message):
        smoke.load(write(tmp_path, body))


def test_every_problem_is_reported_at_once(tmp_path):
    body = "serials:\n  FHRC28: K1\n  FHRC36: K1\nquestion: ''\nkeywords: []\n"
    with pytest.raises(smoke.ConfigError) as err:
        smoke.load(write(tmp_path, body))
    text = str(err.value)
    for part in ("no serial for VHRS28, VHRS36", "K1 is given for both", "'question' is empty", "'keywords'", "'image'"):
        assert part in text


def test_a_run_uses_a_fixed_hopper_model_and_its_serial():
    config = smoke.load()
    for seed in range(40):
        s = smoke.choose(seed)
        assert s.model in smoke.SMOKE_MODELS
        assert s.serial == config.serials[s.model]
        assert (s.question, s.keywords, s.image, s.pinned) == (config.question, config.keywords, config.image, "")


def test_runs_use_both_fixed_hopper_models():
    assert {smoke.choose(seed).model for seed in range(40)} == set(smoke.SMOKE_MODELS)


def test_same_seed_same_selection():
    assert smoke.choose(7).as_dict() == smoke.choose(7).as_dict()


def test_kb_seed_is_used_when_no_seed_is_given(monkeypatch):
    monkeypatch.setenv("KB_SEED", "1234")
    assert smoke.choose().seed == 1234


def test_kb_model_pin_uses_that_models_serial(monkeypatch):
    monkeypatch.setenv("KB_MODEL", " vhrs36 ")
    s = smoke.choose(3)
    assert (s.model, s.serial, s.pinned) == ("VHRS36", smoke.load().serials["VHRS36"], "KB_MODEL")


def test_kb_model_must_be_one_of_the_four(monkeypatch):
    monkeypatch.setenv("KB_MODEL", "FHRC26")
    with pytest.raises(LookupError, match="KB_MODEL='FHRC26' is not one of"):
        smoke.choose(1)


def test_selection_as_dict_is_what_the_report_reads():
    d = smoke.choose(5).as_dict()
    assert set(d) == {"seed", "pinned", "model", "serial", "question", "keywords", "image"}
    assert d["keywords"] and all(set(k) == {"term", "synonyms"} for k in d["keywords"])
