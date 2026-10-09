"""Loads the agent's settings.yaml and phrases.yaml straight from the agent repo.

The files are never copied into this repo: AGENT_SRC points at a checkout of
thinknetic-livekit-agents (CI checks it out fresh each run), so these tests always
judge what the agent team last committed.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_REL = "src/assistants/product_support/config/enterprises-product-support-assistant"
# Local default: the agent repo checked out next to this one.
DEFAULT_SRC = Path(__file__).resolve().parents[3].parent / "thinknetic-livekit-agents"


class SettingsNotFound(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    directory: Path
    settings: dict      # the `system_settings:` block
    phrases: dict
    raw: dict           # whole parsed settings.yaml, for top-level key checks
    sha256: str


def config_dir() -> Path:
    src = Path(os.getenv("AGENT_SRC") or DEFAULT_SRC)
    return src / (os.getenv("SETTINGS_REL") or DEFAULT_REL)


def load() -> Config:
    d = config_dir()
    sfile, pfile = d / "settings.yaml", d / "phrases.yaml"
    for f in (sfile, pfile):
        if not f.is_file():
            raise SettingsNotFound(
                f"{f} not found - set AGENT_SRC to a checkout of thinknetic-livekit-agents"
            )
    text = sfile.read_text()
    raw = yaml.safe_load(text)
    return Config(
        directory=d,
        settings=(raw or {}).get("system_settings") or {},
        phrases=yaml.safe_load(pfile.read_text()) or {},
        raw=raw or {},
        sha256=hashlib.sha256(text.encode()).hexdigest(),
    )
