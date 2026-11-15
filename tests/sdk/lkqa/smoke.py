"""
The live call's fixed inputs (kb/smoke.yaml) and how one run picks from them.

kb/smoke.yaml holds one serial per classification (machine model), the one question every call
asks, the keywords its answer must contain, and the one image every call asks to see. Each run
picks FHRC28 or FHRC36 at random (the fixed-hopper models) and so that model's serial; the
question and the image never change. The seed is logged so a run
can be repeated:

    KB_SEED=1234      reproduce a run's model
    KB_MODEL=VHRS28   pin the model, any of the four (its serial is used)
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .env import ROOT
from .validator import Keyword

KB_DIR = ROOT / "kb"
SMOKE = KB_DIR / "smoke.yaml"

MODELS = ("FHRC28", "FHRC36", "VHRS28", "VHRS36")  # the four classifications
SMOKE_MODELS = ("FHRC28", "FHRC36")  # the fixed-hopper models; KB_MODEL can still pin a variable one


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    serials: dict[str, str]  # model -> serial
    question: str
    keywords: tuple[Keyword, ...]
    image: str  # the description of the one knowledge-base image every call asks to see


def load_yaml(path: Path) -> Any:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load(path: Path = SMOKE) -> Config:
    """kb/smoke.yaml, checked. Raises ConfigError naming every problem at once, so a typo stops
    the run before a call is placed."""
    data = load_yaml(path)
    data = data if isinstance(data, dict) else {}
    problems: list[str] = []

    serials: dict[str, str] = {}
    listed = data.get("serials")
    if not isinstance(listed, dict):
        problems.append("'serials' must give one serial under each model name")
        listed = {}
    for model, serial in listed.items():
        model = str(model).strip().upper()
        if model not in MODELS:
            problems.append(f"{model} is not a model name; use {', '.join(MODELS)}")
        elif not isinstance(serial, (str, int)) or isinstance(serial, bool) or not str(serial).strip():
            problems.append(f"{model} needs one serial, written as {model}: K1234")
        else:
            serials[model] = str(serial).strip().upper()
    if missing := [m for m in MODELS if m not in serials and m not in {str(k).strip().upper() for k in listed}]:
        problems.append(f"no serial for {', '.join(missing)}; each model needs one")
    seen: dict[str, str] = {}
    for model, serial in serials.items():
        if serial in seen:
            problems.append(f"{serial} is given for both {seen[serial]} and {model}")
        seen.setdefault(serial, model)

    question = data.get("question")
    if not isinstance(question, str) or not question.strip():
        problems.append("'question' is empty")
        question = ""

    keywords: list[Keyword] = []
    raw = data.get("keywords")
    if not isinstance(raw, list) or not raw:
        problems.append("'keywords' must list at least one keyword")
        raw = []
    for item in raw:
        try:
            kw = Keyword.parse(item)
        except (ValueError, AttributeError, TypeError) as exc:
            problems.append(f"keyword {exc}")
            continue
        if any(kw.forms()[0] == k.forms()[0] for k in keywords):
            problems.append(f"keyword {kw.term!r} is listed twice")
            continue
        keywords.append(kw)

    image = data.get("image")
    if not isinstance(image, str) or not image.strip():
        problems.append("'image' must give the description of one knowledge-base image")
        image = ""

    if problems:
        raise ConfigError(f"{path.name} is not valid:\n  " + "\n  ".join(problems))
    return Config(serials=serials, question=question.strip(), keywords=tuple(keywords),
                  image=" ".join(image.split()))


@dataclass
class Selection:
    seed: int
    model: str
    serial: str
    question: str
    keywords: tuple[Keyword, ...]
    pinned: str  # "KB_MODEL" or ""
    image: str  # the description of the knowledge-base image the caller asks to see

    def as_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "pinned": self.pinned,
            "model": self.model,
            "serial": self.serial,
            "question": self.question,
            "keywords": [{"term": k.term, "synonyms": list(k.synonyms)} for k in self.keywords],
            "image": self.image,
        }


def choose(seed: int | None = None, config: Config | None = None) -> Selection:
    """Check kb/smoke.yaml, then pick the model (and so the serial)."""
    config = config or load()  # raises before any call if the file is malformed
    if seed is None:
        seed = int(os.getenv("KB_SEED") or random.SystemRandom().randrange(1, 10**9))
    pin = os.getenv("KB_MODEL", "").strip().upper()
    if pin:
        if pin not in config.serials:
            raise LookupError(f"KB_MODEL={pin!r} is not one of {', '.join(MODELS)}")
        model = pin
    else:
        model = random.Random(seed).choice(SMOKE_MODELS)
    return Selection(seed=seed, model=model, serial=config.serials[model], question=config.question,
                     keywords=config.keywords, pinned="KB_MODEL" if pin else "", image=config.image)
