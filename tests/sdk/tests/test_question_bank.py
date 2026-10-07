"""kb/question_bank.yaml against the knowledge bases (tools/check_question_bank.py). Offline."""

from __future__ import annotations

import sys

import pytest

from lkqa.routing import KB_FILES, ROOT

sys.path.insert(0, str(ROOT / "tools"))
import check_question_bank as checker  # noqa: E402

pytestmark = pytest.mark.offline

ENTRIES = checker.load()


def test_bank_has_entries_for_every_model():
    assert {e["model"] for e in ENTRIES} == set(KB_FILES)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_entry_is_grounded_in_its_kb_and_satisfiable(entry):
    problems = checker.check_entry(entry, {})
    assert not problems, "\n".join(problems)


def test_ids_are_unique():
    ids = [e["id"] for e in ENTRIES]
    assert len(ids) == len(set(ids))
