"""
Which environment a run targets - nonprod (the default) or prod - and that environment's settings.

QA_ENV picks it. Every setting has one name per environment, the same in .env on a laptop and
in the repository's secrets and variables in CI:

    nonprod   no prefix      LIVEKIT_URL, AGENT_NAME, ...
    prod      PROD_          PROD_LIVEKIT_URL, PROD_AGENT_NAME, ...

A setting is taken from the first of these that has it (a blank value counts as unset):

    1. the process environment, unprefixed: LIVEKIT_URL=... make kb, for one run. In CI every
       setting comes this way: the workflow reads the environment's secret or variable of that
       name (.github/workflows/smoke.yml) and passes it on unprefixed. CI has no .env.
    2. .env, under the environment's name: LIVEKIT_URL for nonprod, PROD_LIVEKIT_URL for prod
    3. .env, settings both environments share (KB_SEED, TEST_CALLER_*)
    4. nonprod only: NONPROD_DEFAULTS below, the agent and product built in

So a nonprod run needs only the LiveKit URL and keys and SMS_TEST_PHONE - in CI, the
repository's four existing secrets. A prod run never takes a nonprod value, from .env or
the defaults, so a blank PROD_ setting stays missing instead of pointing the prod run at nonprod.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
DOTENV = ROOT / ".env"
DEFAULT = "nonprod"
# The environment whose settings carry no prefix. The repository's LIVEKIT_URL, LIVEKIT_API_KEY,
# LIVEKIT_API_SECRET and SMS_TEST_PHONE secrets are nonprod's.
UNPREFIXED = "nonprod"

# Nonprod's agent and the product it supports, as the product backend sends them. Built in, as
# CI had them before the environments; set any of them (in .env, or as a secret or variable) to
# override it. Prod has no defaults.
NONPROD_DEFAULTS = {
    "AGENT_NAME": "thinknetic-agents-nonprod",
    "PRODUCT_NAME": "Chip Spreader",
    "PRODUCT_BRAND": "Etnyre",
    "ORGANIZATION_ID": "11111111-1111-1111-1111-111111111111",
    "ORG_SLUG": "e",
    "KNOWLEDGE_BASE_ID": "34456cd9-49ea-4d87-8edb-9a60b02e0321",
    "ASSISTANT": "enterprises-product-support-assistant",
}

# What the live call cannot run without. The test caller (TEST_CALLER_*) is the same
# everywhere and keeps its defaults in conftest.py.
REQUIRED = (
    "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "AGENT_NAME", "SMS_TEST_PHONE",
    "PRODUCT_NAME", "PRODUCT_BRAND", "ORGANIZATION_ID", "ORG_SLUG", "KNOWLEDGE_BASE_ID", "ASSISTANT",
)
# Set per environment.
PER_ENV = (*REQUIRED, "AGENT_ID")
# Never printed.
SECRETS = ("LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SMS_TEST_PHONE")


def name() -> str:
    return (os.getenv("QA_ENV") or DEFAULT).strip().lower()


def prefix() -> str:
    """'' for nonprod, 'PROD_' for prod."""
    return "" if name() == UNPREFIXED else name().upper() + "_"


def setting_name(key: str) -> str:
    """The name a setting has for this environment, in .env and as a CI secret or variable."""
    return prefix() + key


def _per_env(key: str) -> bool:
    """A per-environment setting under any environment's name: LIVEKIT_URL, PROD_LIVEKIT_URL."""
    return any(key == p or key.endswith("_" + p) for p in PER_ENV)


def _dotenv() -> dict[str, str | None]:
    return dotenv_values(DOTENV) if DOTENV.is_file() else {}


def sections() -> list[str]:
    """The environments .env has a LiveKit URL line for."""
    return sorted({UNPREFIXED if k == "LIVEKIT_URL" else k.removesuffix("_LIVEKIT_URL").lower()
                   for k in _dotenv() if k.endswith("LIVEKIT_URL")})


def load() -> dict[str, str]:
    """Fill os.environ from .env for this environment, never over a value already set.
    Returns where each per-environment setting came from. Call once per process."""
    os.environ["QA_ENV"] = name()
    values = _dotenv()
    candidates = {k: (v, ".env") for k, v in values.items() if not _per_env(k)}
    candidates |= {k: (values.get(setting_name(k)), f".env {setting_name(k)}") for k in PER_ENV}
    origin: dict[str, str] = {}
    for key, (value, source) in candidates.items():
        if os.getenv(key):
            origin[key] = "process environment"
        elif value:
            os.environ[key] = value
            origin[key] = source
    if name() == UNPREFIXED:
        for key, value in NONPROD_DEFAULTS.items():
            if not os.getenv(key):
                os.environ[key] = value
                origin[key] = "built-in default"
    return {k: v for k, v in origin.items() if k in PER_ENV}


def missing() -> list[str]:
    return [k for k in REQUIRED if not os.getenv(k)]


def in_ci() -> bool:
    """A GitHub Actions run: settings come from repository secrets and variables, not .env."""
    return os.getenv("GITHUB_ACTIONS") == "true"


def how_to_set(keys: list[str]) -> str:
    """Where to set missing settings for this run: in CI its secrets or variables, locally .env."""
    names = ", ".join(setting_name(k) for k in keys)
    if in_ci():
        return f"set the repository secret(s) or variable(s) {names} (Settings > Secrets and variables > Actions)"
    return f"set {names} in .env"
