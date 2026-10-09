"""Static checks of the agent's settings.yaml, read fresh from the agent repo.

Offline: no calls are placed. Needs AGENT_SRC (a checkout of
thinknetic-livekit-agents); see lkqa/settings_model.py. A bad edit to the file
fails here before any live call is spent on it.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
import yaml
from jinja2 import Environment, meta

from lkqa import cronwindow, settings_model

pytestmark = pytest.mark.settings

ROOT = Path(__file__).resolve().parents[3]
E164 = re.compile(r"^\+[1-9]\d{6,14}$")
DTMF = re.compile(r"^[0-9*#A-Dw]+$")
EXPECT = yaml.safe_load((ROOT / "kb" / "settings_expectations.yaml").read_text())


@pytest.fixture(scope="session")
def cfg():
    try:
        return settings_model.load()
    except settings_model.SettingsNotFound as e:
        pytest.fail(str(e), pytrace=False)


@pytest.fixture(scope="session")
def S(cfg):
    return cfg.settings


def _destinations(S):
    return S["transfer"]["destinations"]


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)


def test_s01_parses_with_known_keys(cfg):
    assert set(cfg.raw) == set(EXPECT["top_level_keys"])
    unknown = set(cfg.settings) - set(EXPECT["system_settings_keys"])
    assert not unknown, f"unknown system_settings keys (typo, or add to kb/settings_expectations.yaml): {sorted(unknown)}"


def test_s02_s03_kb(S):
    kb = S["kb"]
    assert kb["database_url_env_key"] and re.fullmatch(r"[A-Z][A-Z0-9_]*", kb["database_url_env_key"]), \
        "database_url_env_key must be the NAME of an env var, not a DSN"
    for k in ("hybrid_search_enabled", "hybrid_keyword_search_enabled", "image_search_enabled", "capture_search_metrics"):
        assert isinstance(kb[k], bool), k
    assert 0 < kb["max_distance"] <= 2
    assert 0 < kb["image_max_distance"] <= 2
    assert kb["image_max_distance"] <= kb["max_distance"]
    assert kb["filler_after_seconds"] >= 0
    assert kb["image_timeout_seconds"] > 0


def test_s04_resume_days(S):
    v = S["resume_last_session_within_days"]
    assert isinstance(v, int) and not isinstance(v, bool) and v >= 0


def test_s05_serial_formats_cover_smoke_serials(S):
    fmts = S["serial_number_formats"]
    assert fmts and all(re.fullmatch(r"[A#\W]+", f) for f in fmts), f"only A, # and punctuation allowed: {fmts}"

    def fits(serial: str, fmt: str) -> bool:
        pat = [c for c in fmt if c in "A#"]
        if len(pat) != len(serial):
            return False
        return all(c.isalpha() if p == "A" else c.isdigit() for p, c in zip(pat, serial))

    serials = yaml.safe_load((ROOT / "kb" / "smoke_serials.yaml").read_text())["serials"]
    bad = [s["serial"] for s in serials if not any(fits(s["serial"], f) for f in fmts)]
    assert not bad, f"smoke serials that no serial_number_formats shape accepts: {bad}"


def test_s06_pronunciations(S):
    seen: dict[str, str] = {}
    for respelling, spellings in S["pronunciations"].items():
        assert isinstance(respelling, str) and respelling.strip()
        assert spellings and all(isinstance(x, str) and x.strip() for x in spellings), respelling
        for sp in spellings:
            key = sp.lower()
            assert key not in seen, f"{sp!r} is under both {seen[key]!r} and {respelling!r}"
            seen[key] = respelling


def test_s07_s08_http_endpoints(S, cfg):
    tools = S["integrations"]["http_endpoints"]
    for name, ep in tools.items():
        assert ep["url"].startswith("https://"), f"{name}: url must be https"
        assert ep.get("method", "POST").upper() in EXPECT["http_methods"]
        assert ep.get("timeout_seconds", 1) > 0
        cred = ep["credentials"]
        assert cred["type"] in EXPECT["credential_types"]
        assert re.fullmatch(r"[A-Z][A-Z0-9_]*", cred["env_key"]), f"{name}: env_key must be a variable NAME, not a token"
        # "Better no tool than one that fails": every configured tool must be described to the model.
        p = cfg.phrases
        assert name in p["tool_schema"], f"{name}: no tool_schema.{name} in phrases.yaml"
        assert p["instructions"]["error"].get(f"{name}_failed"), f"{name}: no instructions.error.{name}_failed"
    assert cfg.phrases["say"].get("arranging_callback"), "say.arranging_callback missing in phrases.yaml"


def test_s09_callback_body_renders(S):
    ep = S["integrations"]["http_endpoints"]["request_callback"]
    env = Environment()
    text = yaml.safe_dump(ep["body_template"])
    # Blank values must hit the default("NA", true) path and still give a non-empty line.
    out = env.from_string(text).render(reason="r", phone_number="", room_id="", product_serial_number="", product_id="")
    assert "{{" not in out and "NA" in out
    yaml.safe_load(out)  # still valid structure


def test_s10_sms(S):
    assert E164.match(S["sms"]["from_number"])
    assert str(S["sms"]["default_country_code"]).isdigit()


def test_s11_s12_transfer(S, cfg):
    t = S["transfer"]
    try:
        ZoneInfo(t["timezone"])
    except (ZoneInfoNotFoundError, ValueError):
        pytest.fail(f"timezone {t['timezone']!r} is not an IANA name")
    assert t["timeout_seconds"] > 0 and t["sip_trunk_id"]
    enum = cfg.phrases["tool_schema"]["transfer_to_human"]["parameters"]["properties"]["keyword"]["enum"]
    for d in t["destinations"]:
        assert set(d["keywords"]) <= set(enum), f"{d['description']}: keywords {d['keywords']} not in {enum}"
        assert E164.match(d["to_number"]) and E164.match(d["from_number"]), d["description"]
        if d.get("dtmf"):
            assert DTMF.match(d["dtmf"]), f"{d['description']}: bad dtmf {d['dtmf']!r}"
        for c in d.get("available", []):
            assert len(c.split()) == 5, f"bad cron {c!r}"


def test_s13_transfer_coverage(S, cfg):
    """Every minute of the week has a desk open for each keyword. Overlaps are fine
    (the first open destination wins, as settings.yaml documents) and are only reported."""
    t = S["transfer"]
    enum = cfg.phrases["tool_schema"]["transfer_to_human"]["parameters"]["properties"]["keyword"]["enum"]
    for kw in enum:
        grid = cronwindow.week_grid(t["destinations"], kw)
        gaps = [(cronwindow.MONDAY + timedelta(minutes=m)).strftime("%a %H:%M")
                for m, o in enumerate(grid) if not o]
        assert not gaps, f"keyword {kw!r}: {len(gaps)} minutes with no open desk, first: {gaps[:5]}"
        overlaps = sum(1 for o in grid if len(o) > 1)
        print(f"   [s13] {kw}: {overlaps} overlapping minute(s) per week (first open desk wins)")


@pytest.mark.parametrize(
    ("kw", "when", "expect_desc"),
    [
        ("part", "2026-01-05 06:59", "after-hours"),   # Mon, just before the day desk opens
        ("part", "2026-01-05 07:00", "business hours"),
        ("part", "2026-01-05 16:59", "business hours"),
        ("part", "2026-01-05 17:00", "business hours"),  # the 17:00 minute still belongs to the day desk
        ("part", "2026-01-05 17:01", "after-hours"),
        ("other", "2026-01-10 00:00", "after-hours"),  # Sat
        ("other", "2026-01-11 23:59", "after-hours"),  # Sun
    ],
)
def test_s13_edge_minutes(S, kw, when, expect_desc):
    t = S["transfer"]
    now = datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(t["timezone"]))
    d = cronwindow.first_open(t["destinations"], kw, t["timezone"], now)
    assert d is not None and expect_desc in d["description"], f"{kw} at {when}: got {d and d['description']}"


def test_s14_transfer_numbers_are_test_numbers(S):
    allow = {n.strip() for n in os.getenv("TRANSFER_TEST_NUMBERS", "").split(",") if n.strip()}
    if not allow:
        pytest.skip("TRANSFER_TEST_NUMBERS not set - cannot tell a test desk from a real one")
    real = {d["to_number"] for d in _destinations(S)} - allow
    assert not real, f"transfer destinations outside the test-number allow-list: {sorted(real)}"


def test_s15_s16_models(S):
    tr = S["transcriber"]
    assert tr["model"] in EXPECT["transcribers"].get(tr["provider"], []), f"transcriber {tr['provider']}/{tr['model']}"
    for k in ("smart_format", "numerals", "profanity_filter"):
        assert isinstance(tr[k], bool)
    m = S["model"]
    assert m["model"] in EXPECT["llms"].get(m["provider"], []), f"model {m['provider']}/{m['model']} not in allow-list"
    assert 0 <= m["temperature"] <= 2 and 1 <= m["max_tool_steps"] <= 50


def test_s17_voice_chain(S):
    voices = S["voice"]
    assert isinstance(voices, list) and len(voices) >= 2, "voice needs a primary and at least one fallback provider"
    for v in voices:
        assert v["provider"] in EXPECT["voice_providers"]
        if v["provider"] == "cartesia":
            assert v["voice"] and 0.6 <= v["speed"] <= 1.5
        if v["provider"] == "elevenlabs":
            assert v["voice_id"]
    assert len({v["provider"] for v in voices}) >= 2, "fallback should be a different provider"


def test_s18_s19_pipeline(S):
    assert isinstance(S["noise_cancellation"]["enabled"], bool)
    th = S["turn_handling"]
    assert th["turn_model"] in EXPECT["turn_models"]
    assert th["endpointing"]["mode"] in EXPECT["endpointing_modes"]
    assert 0 <= th["endpointing"]["min_delay"] <= th["endpointing"]["max_delay"]
    assert th["interruption"]["min_words"] >= 0 and th["interruption"]["min_duration"] >= 0


def test_s20_s21_message_plan(S):
    mp = S["message_plan"]
    assert mp["idle_timeout_seconds"] > 0 and mp["idle_message_max_spoken_count"] >= 1
    assert mp["idle_messages"] and all(m.strip() for m in mp["idle_messages"])
    cap = S["max_duration_seconds"]
    assert cap >= 0
    if cap:
        assert cap > mp["idle_timeout_seconds"] * mp["idle_message_max_spoken_count"]


def test_s22_structured_data_schema(S):
    sd = S["end_call"]["structured_data"]
    schema = sd["schema"]
    assert schema["type"] == "object" and schema.get("additionalProperties") is False
    assert set(schema["required"]) <= set(schema["properties"])
    for name, prop in schema["properties"].items():
        assert "type" in prop and prop.get("description"), name


def test_s23_webhook(S):
    from urllib.parse import urlparse
    u = urlparse(S["end_call"]["webhook"]["url"])
    assert u.scheme == "https" and u.hostname not in ("localhost", "127.0.0.1")
    assert u.hostname in EXPECT["webhook_hosts"], f"webhook host {u.hostname} not in allow-list"


def test_s24_placeholders_are_known(S):
    env = Environment()
    known = set(EXPECT["known_placeholders"])
    unknown = set()
    for s in _strings(S):
        unknown |= meta.find_undeclared_variables(env.parse(s)) - known
    assert not unknown, f"placeholders the tests do not know about (typo, or add to kb/settings_expectations.yaml): {sorted(unknown)}"


def test_s25_hash_is_reported(cfg):
    print(f"   [s25] settings.yaml sha256 {cfg.sha256} ({cfg.directory})")
    assert len(cfg.sha256) == 64
