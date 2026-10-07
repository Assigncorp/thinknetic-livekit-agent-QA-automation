"""
Serial -> model -> knowledge base, from kb/hopper_classification.xlsx.

Only the two classified sheets route. The raw BOM sheets (`RC36`, `RC28`) are
reference material: a serial's BOM can list a controller it no longer has
(K7170 carried an RC36 computer for three weeks in 2017), so routing from them
would send a call to the wrong KB.

| Sheet           | Hopper Type | Model  |
|-----------------|-------------|--------|
| RC28 Classified | VARIABLE    | VHRS28 |
| RC28 Classified | FIXED       | FHRC28 |
| RC36 Classified | VARIABLE    | VHRS36 |
| RC36 Classified | FIXED       | FHRC36 |

The two sheets put their columns in different places, so every column is found
by its header name.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KB_DIR = ROOT / "kb"
WORKBOOK = KB_DIR / "hopper_classification.xlsx"
SMOKE_SERIALS = KB_DIR / "smoke_serials.yaml"

KB_FILES = {
    "VHRS28": "2026-08-07-vhrs28-voice-agent-knowledge-base.md",
    "VHRS36": "2026-08-07-vhrs36-voice-agent-knowledge-base.md",
    "FHRC36": "2026-08-17-FHRC36-VoiceAgent-Knowledge-Base.md",
    "FHRC28": "2026-09-24-fhrc28-voice-agent-knowledge-base.md",
}

ROUTES = {
    ("RC28 Classified", "VARIABLE"): "VHRS28",
    ("RC28 Classified", "FIXED"): "FHRC28",
    ("RC36 Classified", "VARIABLE"): "VHRS36",
    ("RC36 Classified", "FIXED"): "FHRC36",
}

# A basis that starts like this was classified from the parent description
# itself; anything else ("Inferred from child part descriptions…", "TIE in
# child evidence…") is a weaker guess and is not used for smoke serials.
DIRECT_BASIS_PREFIX = "parent description"


class UnknownSerialError(LookupError):
    pass


class RoutingError(AssertionError):
    pass


@dataclass(frozen=True)
class Classification:
    serial: str
    sheet: str
    parent_description: str
    hopper_type: str
    basis: str

    @property
    def model(self) -> str:
        return ROUTES[(self.sheet, self.hopper_type)]

    @property
    def kb_file(self) -> str:
        return KB_FILES[self.model]

    @property
    def kb_path(self) -> Path:
        return KB_DIR / self.kb_file

    @property
    def direct(self) -> bool:
        return self.basis.strip().lower().startswith(DIRECT_BASIS_PREFIX)


def _norm_serial(serial: str) -> str:
    return str(serial).strip().upper()


@lru_cache(maxsize=None)
def _index(workbook: Path = WORKBOOK) -> dict[str, Classification]:
    import openpyxl

    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    found: dict[str, Classification] = {}
    for sheet in ("RC28 Classified", "RC36 Classified"):
        rows = wb[sheet].iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(rows)]
        col = {name: header.index(name) for name in
               ("Parent Part Number", "Parent Description", "Hopper Type", "Classification Basis")}
        for row in rows:
            serial = row[col["Parent Part Number"]]
            if not serial:
                continue
            key = _norm_serial(serial)
            hopper = str(row[col["Hopper Type"]] or "").strip().upper()
            if (sheet, hopper) not in ROUTES:
                raise RoutingError(f"{workbook.name}: {sheet} row {key} has Hopper Type {hopper!r}")
            if key in found:
                raise RoutingError(
                    f"{workbook.name}: serial {key} is in both {found[key].sheet} and {sheet}"
                )
            found[key] = Classification(
                serial=key,
                sheet=sheet,
                parent_description=str(row[col["Parent Description"]] or "").strip(),
                hopper_type=hopper,
                basis=str(row[col["Classification Basis"]] or "").strip(),
            )
    wb.close()
    return found


def classify(serial: str) -> Classification:
    """The workbook row for a serial. Raises UnknownSerialError if it has none."""
    key = _norm_serial(serial)
    try:
        return _index()[key]
    except KeyError:
        raise UnknownSerialError(
            f"serial {key!r} is not in the 'RC28 Classified' or 'RC36 Classified' sheet of "
            f"{WORKBOOK.relative_to(ROOT)}, so there is no knowledge base to test it against"
        ) from None


def kb_for_serial(serial: str) -> tuple[str, str]:
    """(model, kb_file) for a serial, e.g. ('VHRS28', '2026-08-07-vhrs28-…md')."""
    c = classify(serial)
    return c.model, c.kb_file


def smoke_serials() -> list[dict[str, str]]:
    import yaml

    return yaml.safe_load(SMOKE_SERIALS.read_text(encoding="utf-8"))["serials"]


def verify_smoke_serials() -> dict[str, Classification]:
    """Every smoke serial still routes, directly, to the model it is listed for.

    Returns {model: Classification}. Raises RoutingError naming every serial
    that does not, so a workbook update that reclassifies one stops the run
    before a call is placed against the wrong KB.
    """
    problems: list[str] = []
    out: dict[str, Classification] = {}
    for entry in smoke_serials():
        serial, expected = entry["serial"], entry["model"]
        try:
            c = classify(serial)
        except UnknownSerialError as exc:
            problems.append(str(exc))
            continue
        if c.model != expected:
            problems.append(
                f"{serial} is listed as {expected} in {SMOKE_SERIALS.name} but the workbook routes "
                f"it to {c.model} ({c.sheet}, {c.hopper_type})"
            )
        if not c.direct:
            problems.append(
                f"{serial} is not classified from its parent description (basis: {c.basis!r}); "
                f"smoke serials must be"
            )
        if entry.get("sheet") and entry["sheet"] != c.sheet:
            problems.append(f"{serial} is listed on sheet {entry['sheet']!r} but is on {c.sheet!r}")
        out[expected] = c
    missing = set(KB_FILES) - set(out)
    if missing:
        problems.append(f"{SMOKE_SERIALS.name} has no serial for {sorted(missing)}")
    if problems:
        raise RoutingError("smoke serials do not route as listed:\n  " + "\n  ".join(problems))
    return out
