"""
Matching a KB fact against what the agent actually says.

A faithful port of ui/src/utils/anchors.ts. The duplication is deliberate and
the alternative is worse: the browser suite and this one must agree on whether
an answer cited `400 FPM`, because when they disagree the report says the agent
both did and did not cite the manual, and nobody can tell which half is wrong.
Two implementations of one rule, tested against the same cases, beats a
cross-language bridge for eighty lines of regex.

test_rubric_catalog.py asserts the two stay in step by running the TypeScript
suite's own fixtures through this. If you change one, change both.

The rule itself, from the TS original: the agent is voice-first and writes the
way it talks, so `400 FPM` comes back as "four hundred feet per minute" and
`2,500 FPM` as "twenty five hundred feet per minute". An anchor matches if
EITHER form appears - digits or words, unit abbreviated or spelled out.
"""

from __future__ import annotations

import re

UNITS: dict[str, list[str]] = {
    "fpm": ["fpm", "feet per minute", "ft per minute", "feet/minute"],
    "psi": ["psi", "pounds per square inch", "pounds of pressure"],
    "rpm": ["rpm", "revolutions per minute", "revs per minute"],
    "vdc": ["vdc", "volts dc", "volts d c", "volts", "volt"],
    "volts": ["volts", "volt", "vdc"],
    "volt": ["volt", "volts", "vdc"],
    "amps": ["amps", "amp", "amperes", "amperage"],
    "amp": ["amp", "amps", "amperes"],
    "ohms": ["ohms", "ohm"],
    "ohm": ["ohm", "ohms"],
    "gallons": ["gallons", "gallon", "gal"],
    "gallon": ["gallon", "gallons", "gal"],
    # "240°F" is spoken "two hundred forty degrees" - usually without the "F".
    "f": ["f", "°f", "degrees f", "degrees fahrenheit", "degrees", "degree"],
    "inch": ["inch", "inches", '"'],
    "inches": ["inches", "inch", '"'],
}

ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

MEASUREMENT = re.compile(r'^([\d.,/]+)\s*°?\s*([A-Za-z"]+)$')


def _under_100(v: int) -> str:
    if v < 20:
        return ONES[v]
    tens = TENS[v // 10]
    ones = v % 10
    return tens if ones == 0 else f"{tens} {ONES[ones]}"


def _under_1000(v: int) -> str:
    if v < 100:
        return _under_100(v)
    hundreds = f"{ONES[v // 100]} hundred"
    rest = v % 100
    return hundreds if rest == 0 else f"{hundreds} {_under_100(rest)}"


def spell_integer(n: int) -> list[str]:
    """Spellings an integer may be spoken as: 2500 -> 'two thousand five
    hundred' and 'twenty five hundred'."""
    if n < 0 or n > 999_999:
        return []

    forms: list[str] = []

    def add(form: str) -> None:
        if form not in forms:
            forms.append(form)

    if n < 1000:
        add(_under_1000(n))
    else:
        thousands, rest = divmod(n, 1000)
        base = f"{_under_1000(thousands)} thousand"
        add(base if rest == 0 else f"{base} {_under_1000(rest)}")
        # "twenty five hundred" for 2500 - how people actually say these.
        if n < 10_000 and n % 100 == 0:
            add(f"{_under_100(n // 100)} hundred")

    return forms


def _loose(s: str) -> str:
    """
    Escaped, with whitespace loosened so 'four  hundred' and 'four-hundred'
    both match.

    Split-then-escape, NOT escape-then-substitute. Python's re.escape escapes
    `-` and whitespace where the TypeScript original's hand-rolled escape does
    not, so substituting a separator class over an already-escaped string
    replaces the `-` and strands the backslash in front of it. `P1-PIN 21`
    became `P1\\[\\s-]*PIN`, which matches nothing - and it failed silently,
    scoring every pin-reference anchor as uncited.
    """
    parts = [re.escape(part) for part in re.split(r"[\s\-]+", s) if part]
    return r"[\s-]*".join(parts) if parts else re.escape(s)


def _bounded(pattern: str) -> str:
    """
    Stop an anchor matching inside a longer number.

    Anchors like `0 PSI`, `0 VDC` and `0.00 amps` are real - they are how the
    KBs write "you should read nothing here". Matched as bare substrings they
    fire on `400 PSI`, so an answer citing the charge pressure was credited
    with citing the zero reading too, and anchorCoverage scored 3/3 on an
    answer that covered 2. \b is not enough on its own because it treats `.`
    as a boundary, so `0.00 amps` would still match inside `10.00 amps`.
    """
    return rf"(?<![0-9A-Za-z.]){pattern}(?![0-9A-Za-z])"


def anchor_patterns(anchor: str) -> list[re.Pattern[str]]:
    """Every way the agent might write this KB fact."""
    trimmed = anchor.strip()
    patterns: list[str] = [_loose(trimmed)]

    def add(p: str) -> None:
        if p not in patterns:
            patterns.append(p)

    # "240°F" and '1/16"' both split into a number and a unit; the degree sign
    # is dropped because the spoken form never has it.
    match = MEASUREMENT.match(trimmed)
    if match:
        raw_number, raw_unit = match.group(1), match.group(2)
        units = UNITS.get(raw_unit.lower(), [raw_unit.lower()])

        number_forms = [raw_number, raw_number.replace(",", "")]
        try:
            numeric = float(raw_number.replace(",", ""))
        except ValueError:
            numeric = None
        if numeric is not None:
            as_int = int(numeric)
            if numeric == as_int:
                if str(as_int) not in number_forms:
                    number_forms.append(str(as_int))
                number_forms.extend(spell_integer(as_int))

        for num in number_forms:
            for unit in units:
                add(rf"{_loose(num)}[\s-]*{_loose(unit)}")

    return [re.compile(_bounded(p), re.IGNORECASE) for p in patterns]


def bare_number_patterns(number: str) -> list[re.Pattern[str]]:
    """Every way a number alone might be written, bounded the same way an
    anchor is.

    Exposed rather than inlined by a caller because the bounding rule - do not
    match inside a longer number - is the same rule, and a second copy of it
    is a second place for `0` to start matching inside `400`.
    """
    forms = [number]
    try:
        numeric = float(number.replace(",", ""))
    except ValueError:
        numeric = None
    if numeric is not None and numeric == int(numeric):
        as_int = int(numeric)
        if str(as_int) not in forms:
            forms.append(str(as_int))
        forms.extend(spell_integer(as_int))
    return [re.compile(_bounded(_loose(f)), re.IGNORECASE) for f in forms]


def cites_anchor(answer: str, anchor: str) -> bool:
    """Does the agent's reply cite this KB fact, written or spoken?"""
    return any(p.search(answer) for p in anchor_patterns(anchor))


def cited_anchors(answer: str, anchors: list[str]) -> list[str]:
    """The KB facts the reply cites - empty means it cited none of them."""
    return [a for a in anchors if cites_anchor(answer, a)]
