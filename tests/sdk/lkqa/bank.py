"""
The question bank (kb/question_bank.yaml) and how one run picks from it.

Each run picks one of the four smoke models at random, routes its smoke serial
through the workbook, and picks one bank entry FOR THAT MODEL - a question from
another model's KB is never asked. The seed is logged so a run can be repeated:

    KB_SEED=1234            reproduce a run's model and question
    KB_MODEL=FHRC28         pin the model (its smoke serial is used)
    KB_QUESTION_ID=…        pin one entry (its model is used)
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Any

from .routing import KB_DIR, Classification, verify_smoke_serials

BANK = KB_DIR / "question_bank.yaml"


def load_bank() -> list[dict[str, Any]]:
    import yaml

    data = yaml.safe_load(BANK.read_text(encoding="utf-8"))
    return data["entries"] if isinstance(data, dict) else data


@dataclass
class Selection:
    seed: int
    model: str
    serial: str
    classification: Classification
    entry: dict[str, Any]
    pinned: str  # "", "KB_MODEL", "KB_QUESTION_ID"

    def as_dict(self) -> dict[str, Any]:
        c = self.classification
        return {
            "seed": self.seed,
            "pinned": self.pinned,
            "model": self.model,
            "serial": self.serial,
            "sheet": c.sheet,
            "parentDescription": c.parent_description,
            "hopperType": c.hopper_type,
            "classificationBasis": c.basis,
            "kbFile": c.kb_file,
            "questionId": self.entry["id"],
            "kbSection": self.entry["kb_section"],
            "question": self.entry["question"],
        }


def choose(seed: int | None = None) -> Selection:
    """Verify the smoke serials, then pick model + serial + entry."""
    routed = verify_smoke_serials()  # raises before any call if the workbook moved
    bank = load_bank()
    if seed is None:
        seed = int(os.getenv("KB_SEED") or random.SystemRandom().randrange(1, 10**9))
    rng = random.Random(seed)

    pinned = ""
    qid = os.getenv("KB_QUESTION_ID", "").strip()
    pin_model = os.getenv("KB_MODEL", "").strip().upper()
    if qid:
        matches = [e for e in bank if e["id"] == qid]
        if not matches:
            raise LookupError(f"KB_QUESTION_ID={qid!r} is not in {BANK.name}")
        entry, model, pinned = matches[0], matches[0]["model"], "KB_QUESTION_ID"
    else:
        if pin_model:
            if pin_model not in routed:
                raise LookupError(f"KB_MODEL={pin_model!r} is not one of {sorted(routed)}")
            model, pinned = pin_model, "KB_MODEL"
        else:
            model = rng.choice(sorted(routed))
        pool = [e for e in bank if e["model"] == model]
        if not pool:
            raise LookupError(f"{BANK.name} has no entry for {model}")
        entry = rng.choice(pool)

    c = routed[model]
    if entry["model"] != c.model or entry["kb_file"] != c.kb_file:
        raise AssertionError(
            f"entry {entry['id']} is for {entry['model']} but the call is dispatched for {c.model} "
            f"(serial {c.serial}) - a question from another model's KB is never valid")
    return Selection(seed=seed, model=model, serial=c.serial, classification=c, entry=entry, pinned=pinned)
