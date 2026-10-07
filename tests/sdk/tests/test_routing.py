"""Serial -> model routing from kb/hopper_classification.xlsx. Offline."""

from __future__ import annotations

import pytest

from lkqa import routing

pytestmark = pytest.mark.offline


@pytest.mark.parametrize(
    ("serial", "model", "kb_file"),
    [
        ("K7170", "VHRS28", "2026-08-07-vhrs28-voice-agent-knowledge-base.md"),
        ("K7174", "FHRC28", "2026-09-24-fhrc28-voice-agent-knowledge-base.md"),
        ("K6757", "VHRS36", "2026-08-07-vhrs36-voice-agent-knowledge-base.md"),
        ("K6758", "FHRC36", "2026-08-17-FHRC36-VoiceAgent-Knowledge-Base.md"),
    ],
)
def test_smoke_serial_routes_to_its_model(serial, model, kb_file):
    assert routing.kb_for_serial(serial) == (model, kb_file)
    assert (routing.KB_DIR / kb_file).is_file()


def test_serial_lookup_ignores_case_and_whitespace():
    assert routing.kb_for_serial(" k7170 ") == ("VHRS28", routing.KB_FILES["VHRS28"])


def test_unknown_serial_raises_a_clear_error():
    with pytest.raises(routing.UnknownSerialError, match="K0000.*not in the 'RC28 Classified' or 'RC36 Classified'"):
        routing.kb_for_serial("K0000")


def test_raw_bom_sheets_are_not_used_for_routing():
    """K7170's BOM listed an RC36 computer for three weeks in 2017; the classified
    sheet has it on RC28, and that is what routes."""
    c = routing.classify("K7170")
    assert c.sheet == "RC28 Classified"
    assert c.model == "VHRS28"


def test_classified_sheets_have_the_expected_size_and_no_overlap():
    index = routing._index()
    by_sheet = {}
    for c in index.values():
        by_sheet.setdefault((c.sheet, c.hopper_type), 0)
        by_sheet[(c.sheet, c.hopper_type)] += 1
    assert by_sheet == {
        ("RC36 Classified", "VARIABLE"): 331,
        ("RC36 Classified", "FIXED"): 162,
        ("RC28 Classified", "VARIABLE"): 413,
        ("RC28 Classified", "FIXED"): 44,
    }


def test_every_smoke_serial_is_directly_classified_and_routes_as_listed():
    verified = routing.verify_smoke_serials()
    assert set(verified) == set(routing.KB_FILES)
    for model, c in verified.items():
        assert c.model == model
        assert c.direct, c.basis


def test_inferred_serial_is_flagged_as_not_direct():
    # K6786 has no parent description; its basis is inferred from child parts.
    c = routing.classify("K6786")
    assert not c.direct
    assert c.basis.startswith("Inferred from child part descriptions")
