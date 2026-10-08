"""Reading the texted steps out of the agent's worker logs. Offline.

The lines mirror what `lk agent logs` printed for a real call on the deployed agent.
"""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from lkqa import agentlogs
from lkqa.validator import validate

pytestmark = pytest.mark.offline

ENTRY = yaml.safe_load((Path(__file__).parent / "fixtures" / "validator" / "entry.yaml").read_text(encoding="utf-8"))

BODY = "1. Jack the machine up.\n2. Disconnect the 50-pin connector.\nCAUTION: Do not crank engine with gate valve closed."


def line(message: str, room: str = "qa-kb-1", name: str = "tool.external-actions") -> dict:
    return {"message": message, "level": "INFO", "name": name, "room": room, "timestamp": "2026-10-08T06:00:43.989+00:00"}


def test_the_text_body_is_read_back_exactly():
    logged = f"sending_text to=+14805550142 from=+18185729960 message={BODY!r}"
    [sent] = agentlogs.sent_texts([line("phone_number_confirmed to=+14805550142"), line(logged)])
    assert sent["to"] == "+14805550142"
    assert sent["message"] == BODY


def test_no_text_means_no_entries():
    assert agentlogs.sent_texts([line("call_started"), line("images_shown")]) == []


def test_a_rejected_text_reports_why():
    lines = [line("sms_send_rejected to=+14805550142 code=21614 chars=1066 parts=1 reason=that number can't receive texts - it looks like a landline"),
             line("text_failed to=+14805550142 reason=that number can't receive texts - it looks like a landline error=SmsSendError Traceback ...")]
    assert agentlogs.text_failures(lines) == ["that number can't receive texts - it looks like a landline"] * 2
    assert agentlogs.text_failures([line("sending_text to=+1 from=+1 message='x'")]) == []


def test_render_is_one_readable_line_each():
    [out] = agentlogs.render([line("hello")])
    assert out.startswith("2026-10-08T06:00:43.989 INFO") and out.endswith("tool.external-actions: hello")


def test_a_logged_text_is_validated_like_a_spoken_answer():
    full = ("1. Jack the machine up and support securely on stands with all four wheels off the ground.\n"
            "2. Disconnect the 50-pin connector at the engine so engine can only be cranked, not started.")
    v = validate(ENTRY, [full])
    assert 0 < v.score < 1  # two of the entry's steps only: the rest are missing
    assert not v.meets_threshold()
