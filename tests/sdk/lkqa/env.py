"""
Which environment a run targets (SIT, UAT, PROD, ...) and that environment's settings.

QA_ENV picks it; unset means sit. Every environment lives in the one .env file, a section
each, with its name as the prefix of every setting: with QA_ENV=uat the suite's LIVEKIT_URL
is UAT_LIVEKIT_URL. Adding an environment is adding a section; changing a URL is changing
one line. CI writes the same file from the ENV_FILE secret.

A setting is taken from the first of these that has it (a blank value counts as unset):

    1. the process environment, unprefixed: LIVEKIT_URL=... make kb, for one run
    2. .env, the environment's section: UAT_LIVEKIT_URL
    3. .env, unprefixed: only settings shared by every environment (KB_SEED, TEST_CALLER_*)

A per-environment setting is never taken unprefixed from .env, so a blank in one section
can never pick up another environment's value.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
DOTENV = ROOT / ".env"
DEFAULT = "sit"

# What the live call cannot run without. The test caller (TEST_CALLER_*) is the same
# everywhere and keeps its defaults in conftest.py.
REQUIRED = (
    "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "AGENT_NAME", "SMS_TEST_PHONE",
    "PRODUCT_NAME", "PRODUCT_BRAND", "ORGANIZATION_ID", "ORG_SLUG", "KNOWLEDGE_BASE_ID", "ASSISTANT",
)
# Set per environment, in its section of .env.
PER_ENV = (*REQUIRED, "AGENT_ID")
# Never printed.
SECRETS = ("LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SMS_TEST_PHONE")


def name() -> str:
    return (os.getenv("QA_ENV") or DEFAULT).strip().lower()


def prefix() -> str:
    return name().upper() + "_"


def _dotenv() -> dict[str, str | None]:
    return dotenv_values(DOTENV) if DOTENV.is_file() else {}


def sections() -> list[str]:
    """The environments .env has a section for."""
    return sorted(k.removesuffix("_LIVEKIT_URL").lower() for k in _dotenv() if k.endswith("_LIVEKIT_URL"))


def load() -> dict[str, str]:
    """Fill os.environ from .env for this environment, never over a value already set.
    Returns where each per-environment setting came from. Call once per process."""
    os.environ["QA_ENV"] = name()
    pre = prefix()
    values = _dotenv()
    section = {k.removeprefix(pre): (v, f".env {k}") for k, v in values.items() if k.startswith(pre)}
    shared = {k: (v, ".env") for k, v in values.items()
              if not any(k == p or k.endswith("_" + p) for p in PER_ENV)}
    origin: dict[str, str] = {}
    for key, (value, source) in {**shared, **section}.items():
        if os.getenv(key):
            origin[key] = "process environment"
        elif value:
            os.environ[key] = value
            origin[key] = source
    return {k: v for k, v in origin.items() if k in PER_ENV}


def missing() -> list[str]:
    return [k for k in REQUIRED if not os.getenv(k)]
