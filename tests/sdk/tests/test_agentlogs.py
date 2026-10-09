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


CALLER = "4805550142"
SMS = "6025550199"


def test_numbers_compare_by_their_ten_digits():
    assert agentlogs.last10("+1 (602) 555-0199") == agentlogs.last10("+16025550199") == SMS
    assert agentlogs.mask("+16025550199") == "number ending 0199"


@pytest.mark.parametrize(("sms", "fragment"), [
    ("", "is not set"),
    ("   ", "is not set"),
    ("12345", "10-digit"),
    ("+1 480 555 0142", "same as the caller"),
    ("4805550142", "same as the caller"),
])
def test_an_unusable_sms_number_is_rejected_with_a_reason(sms, fragment):
    assert fragment in agentlogs.sms_number_problem(sms, CALLER)


@pytest.mark.parametrize("sms", [SMS, "+16025550199", "(602) 555-0199", "1-602-555-0199"])
def test_a_different_ten_digit_number_is_accepted(sms):
    assert agentlogs.sms_number_problem(sms, CALLER) is None


def test_only_texts_to_the_sms_number_count():
    texts = [{"to": "+14805550142", "message": "a", "timestamp": ""}, {"to": "+16025550199", "message": "b", "timestamp": ""}]
    assert [t["message"] for t in agentlogs.texts_to(texts, SMS)] == ["b"]
    assert agentlogs.texts_to(texts, "6025550100") == []


@pytest.mark.parametrize("spoken", ["6 0 2 5 5 5 0 1 9 9", "602-555-0199", "+1 (602) 555-0199", "6025550199"])
def test_the_published_report_never_carries_the_sms_number(spoken):
    out = agentlogs.redact(f"Please use {spoken}, is that right?", SMS)
    assert "0199" not in out.replace("ending 0199", "") and "[number ending 0199]" in out
    assert agentlogs.redact("no digits here", SMS) == "no digits here"


async def test_the_tail_keeps_only_this_rooms_lines_and_knows_when_the_call_is_done(tmp_path, monkeypatch):
    """A stand-in `lk` prints what `lk agent logs` prints: JSON lines for many rooms."""
    import json
    import stat

    rows = [
        {"message": "call_started", "room": "qa-kb-other", "name": "call"},
        {"message": "sending_text to=+16025550199 from=+1 message='1. Jack it up.'", "room": "qa-kb-mine", "name": "tool.external-actions"},
        {"message": "call_log_delivered status=200", "room": "qa-kb-mine", "name": "call-log"},
        {"message": "call_log_delivered status=200", "room": "qa-kb-other", "name": "call-log"},
    ]
    fake = tmp_path / "lk"
    fake.write_text("#!/bin/sh\ncat <<'EOF'\nUsing agent [CA_x]\n" + "\n".join(json.dumps(r) for r in rows) + "\nEOF\nsleep 30\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")
    monkeypatch.setenv("AGENT_ID", "CA_x")

    tail = agentlogs.LogTail("qa-kb-mine")
    await tail.start()
    try:
        assert await tail.wait_until(lambda lines: bool(agentlogs.texts_to(agentlogs.sent_texts(lines), "6025550199")), 5)
        lines = await tail.finish(5)
    finally:
        await tail.stop()
    assert {o["room"] for o in lines} == {"qa-kb-mine"}
    assert tail.done_seen and len(lines) == 2


# What the deployed agent logged for a real callback request (shortened).
CB_ARGS = "api_call_requested tool=request_callback args={'phone_number': '4805550142', 'reason': 'Caller wants a call back about the engine start.'}"
CB_POST = "calling_api POST https://etnyre-dev.thinknetic.app/api/v1/organizations/1/locations/90001/tasks query=[] body={'title': 'Callback requested'}"
CB_OK = "api_responded https://etnyre-dev.thinknetic.app/api/v1/organizations/1/locations/90001/tasks status=201 chars=1315 in 1370ms"


def test_a_created_callback_task_is_read_from_the_logs():
    lines = [line(CB_ARGS, name="tool.http-request"), line(CB_POST, name="http-request"), line(CB_OK, name="http-request")]
    [task] = agentlogs.callback_tasks(lines)
    assert task["phone"] == "4805550142" and task["status"] == 201 and "engine start" in task["reason"]
    assert agentlogs.callback_created(lines) == task


def test_no_callback_call_means_no_task():
    assert agentlogs.callback_tasks([line("call_started"), line(CB_OK, name="http-request")]) == []
    assert agentlogs.callback_created([]) is None


def test_a_callback_the_task_service_refused_is_not_created():
    refused = CB_OK.replace("status=201", "status=500")
    lines = [line(CB_ARGS), line(refused)]
    assert agentlogs.callback_tasks(lines)[0]["status"] == 500
    assert agentlogs.callback_created(lines) is None


def test_a_callback_with_no_logged_reply_is_not_created():
    assert agentlogs.callback_created([line(CB_ARGS)]) is None


def test_another_apis_reply_is_not_taken_for_the_task_reply():
    other = "api_responded https://x.example/api/v1/lookup status=200 chars=3 in 10ms"
    assert agentlogs.callback_created([line(CB_ARGS), line(other)]) is None


def _rows(*msgs):
    return [{"message": m, "room": "r", "name": "call"} for m in msgs]


def test_call_record_reads_what_the_agent_logged_about_the_record():
    rec = agentlogs.call_record(_rows(
        "voice_session_closed reason=CloseReason.USER_INITIATED",
        "structured_output name=call_analysis by=openai:gpt-4o-mini fields=['call_summary', 'notes'] in 2805ms raw={'call_summary': 'Caller asked', 'notes': ['amber falcon']}",
        "transcript_analyzed turns=31 chars=4000 analyses=['call_analysis'] fields=['call_analysis']",
        "call_summary source=structured_data",
        "call_log_delivered status=200"))
    assert rec["turns"] == 31 and rec["fields"] == ["call_summary", "notes"]
    assert rec["summary_source"] == "structured_data" and rec["delivered"] == 200 and not rec["failure"]
    assert "amber falcon" in rec["analysis"]


def test_call_record_reports_a_failed_delivery_and_an_empty_extraction():
    rec = agentlogs.call_record(_rows("transcript_analyzed turns=0 chars=0 analyses=[] fields=-", "call_log_failed status=500"))
    assert rec["turns"] == 0 and rec["fields"] == [] and rec["delivered"] is None and "500" in rec["failure"]
