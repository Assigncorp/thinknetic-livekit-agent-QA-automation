"""Where a run's settings come from: .env on a laptop, secrets and variables in CI. Offline."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lkqa import env

pytestmark = pytest.mark.offline

WORKFLOW = env.ROOT / ".github" / "workflows" / "smoke.yml"


@pytest.fixture
def clean(monkeypatch):
    """No setting in the process environment; the originals come back after the test."""
    for key in (*env.PER_ENV, "QA_ENV", "KB_SEED", "GITHUB_ACTIONS"):
        monkeypatch.setenv(key, "")
    return monkeypatch


def _dotenv(tmp_path: Path, monkeypatch, body: str) -> None:
    path = tmp_path / ".env"
    path.write_text(body, encoding="utf-8")
    monkeypatch.setattr(env, "DOTENV", path)


@pytest.mark.parametrize(("qa_env", "name"), [("", "LIVEKIT_URL"), ("nonprod", "LIVEKIT_URL"),
                                              ("NONPROD", "LIVEKIT_URL"), ("prod", "PROD_LIVEKIT_URL")])
def test_nonprod_names_have_no_prefix_and_prods_start_with_prod(clean, qa_env, name):
    clean.setenv("QA_ENV", qa_env)
    assert env.setting_name("LIVEKIT_URL") == name


def test_nonprod_reads_the_unprefixed_lines(clean, tmp_path):
    _dotenv(tmp_path, clean, "LIVEKIT_URL=wss://nonprod\nPROD_LIVEKIT_URL=wss://prod\nKB_SEED=7\n")
    origin = env.load()
    assert (env.os.environ["LIVEKIT_URL"], env.os.environ["KB_SEED"]) == ("wss://nonprod", "7")
    assert origin["LIVEKIT_URL"] == ".env LIVEKIT_URL"


def test_prod_reads_prod_lines_and_never_falls_back_to_nonprod(clean, tmp_path):
    _dotenv(tmp_path, clean, "LIVEKIT_URL=wss://nonprod\nAGENT_NAME=nonprod-agent\nPROD_LIVEKIT_URL=wss://prod\n")
    clean.setenv("QA_ENV", "prod")
    env.load()
    assert env.os.environ["LIVEKIT_URL"] == "wss://prod"
    assert "AGENT_NAME" in env.missing()  # PROD_AGENT_NAME is not set; nonprod's is never used


def test_the_process_environment_wins_over_env(clean, tmp_path):
    _dotenv(tmp_path, clean, "LIVEKIT_URL=wss://from-dotenv\n")
    clean.setenv("LIVEKIT_URL", "wss://from-ci")
    assert env.load()["LIVEKIT_URL"] == "process environment"
    assert env.os.environ["LIVEKIT_URL"] == "wss://from-ci"


@pytest.mark.parametrize(("qa_env", "ci", "expected"), [
    ("nonprod", "", "set AGENT_NAME, ORG_SLUG in .env"),
    ("prod", "", "set PROD_AGENT_NAME, PROD_ORG_SLUG in .env"),
    ("nonprod", "true", "set the repository secret(s) or variable(s) AGENT_NAME, ORG_SLUG"),
    ("prod", "true", "set the repository secret(s) or variable(s) PROD_AGENT_NAME, PROD_ORG_SLUG"),
])
def test_a_missing_setting_is_named_where_it_is_set(clean, qa_env, ci, expected):
    clean.setenv("QA_ENV", qa_env)
    clean.setenv("GITHUB_ACTIONS", ci)
    assert env.how_to_set(["AGENT_NAME", "ORG_SLUG"]).startswith(expected)


def _settings_step() -> dict:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["qa"]["steps"]
    return next(s for s in steps if s.get("name", "").startswith("Read the environment's settings"))


def test_ci_reads_every_setting_by_its_name():
    step = _settings_step()
    assert set(step["env"]) == set(env.PER_ENV)
    for key, expr in step["env"].items():
        assert expr.count(f"'{{0}}{key}', env.QA_PREFIX)") == 2, key  # the secret, else the variable
    loop = step["run"].split("for name in", 1)[1].split("; do", 1)[0].replace("\\", " ").split()
    assert sorted(loop) == sorted(env.PER_ENV)  # and every one is passed on to the later steps


def test_ci_prefix_matches_the_names_in_env():
    qa_env = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["qa"]["env"]
    assert qa_env["QA_PREFIX"] == "${{ inputs.environment == 'PROD' && 'PROD_' || '' }}"


def test_nonprod_needs_only_the_four_secrets(clean, tmp_path):
    _dotenv(tmp_path, clean, "")
    origin = env.load()
    assert sorted(env.missing()) == sorted(["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SMS_TEST_PHONE"])
    assert env.os.environ["AGENT_NAME"] == "thinknetic-agents-nonprod"
    assert origin["ORG_SLUG"] == "built-in default"


def test_a_set_value_overrides_the_nonprod_default(clean, tmp_path):
    _dotenv(tmp_path, clean, "AGENT_NAME=agent-from-dotenv\n")
    clean.setenv("PRODUCT_NAME", "Product from a CI variable")
    env.load()
    assert env.os.environ["AGENT_NAME"] == "agent-from-dotenv"
    assert env.os.environ["PRODUCT_NAME"] == "Product from a CI variable"


def test_prod_gets_no_defaults(clean, tmp_path):
    _dotenv(tmp_path, clean, "")
    clean.setenv("QA_ENV", "prod")
    env.load()
    assert set(env.missing()) == set(env.REQUIRED)
