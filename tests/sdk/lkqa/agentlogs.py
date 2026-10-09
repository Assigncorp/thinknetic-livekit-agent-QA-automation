"""
The deployed agent worker's own logs for one call, read with the LiveKit CLI.

The agent runs on LiveKit Cloud. `lk agent logs` replays recent history and then
keeps streaming, one JSON object per line, each carrying the LiveKit room name
in "room". There is no room filter and no end of stream, so: read the stream,
keep the lines for our room, and stop once the call's closing line has shown up
or the stream has gone quiet.

Needs the `lk` CLI on PATH (brew install livekit-cli) and the same LIVEKIT_URL /
LIVEKIT_API_KEY / LIVEKIT_API_SECRET the test already uses. AGENT_ID pins the
agent; otherwise it is looked up by AGENT_NAME.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import Any

# The agent's last words about a call: its record was sent, or could not be. (voice_session_closed
# comes seconds BEFORE the record is analysed and sent, so it is not the end.)
CALL_DONE = ("call_log_delivered", "call_log_failed", "call_log_validation_failed")


def available() -> str | None:
    """None when logs can be read, otherwise why not."""
    if not shutil.which("lk"):
        return "the `lk` CLI is not installed (brew install livekit-cli)"
    return None


async def _run(*args: str, timeout: float = 30) -> str:
    proc = await asyncio.create_subprocess_exec(
        "lk", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise
    return out.decode("utf-8", "replace")


async def agent_id() -> str:
    if os.getenv("AGENT_ID"):
        return os.environ["AGENT_ID"]
    name = os.environ["AGENT_NAME"]
    out = await _run("agent", "list", "--json")
    for agent in json.loads(out[out.index("{"):]).get("agents", []):
        if agent.get("agentName") == name:
            return agent["agentId"]
    raise LookupError(f"no LiveKit Cloud agent named {name!r}")


def parse(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line.startswith("{"):
        return None
    try:
        obj = json.loads(line)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


class LogTail:
    """`lk agent logs` running for the whole call, keeping only the lines for our room.

    Started before the call so the trigger of a text is already there when the call
    reaches it, with no waiting on a fresh replay of the history mid-call. The stream
    replays recent history first, then follows live."""

    def __init__(self, room: str) -> None:
        self.room = room
        self.lines: list[dict[str, Any]] = []
        self.done_seen = False
        self._proc: asyncio.subprocess.Process | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        aid = await agent_id()
        self._proc = await asyncio.create_subprocess_exec(
            "lk", "agent", "logs", "--id", aid, limit=1 << 22,  # tracebacks make long lines
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        self._task = asyncio.create_task(self._pump())

    async def _pump(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        while raw := await self._proc.stdout.readline():
            obj = parse(raw.decode("utf-8", "replace"))
            if obj and obj.get("room") == self.room:
                self.lines.append(obj)
                if any(k in str(obj.get("message", "")) for k in CALL_DONE):
                    self.done_seen = True

    async def wait_until(self, predicate: Any, timeout_s: float) -> bool:
        """True once predicate(lines so far) holds, False at the timeout."""
        loop = asyncio.get_running_loop()
        end = loop.time() + timeout_s
        while loop.time() < end:
            if predicate(self.lines):
                return True
            await asyncio.sleep(0.5)
        return predicate(self.lines)

    async def finish(self, timeout_s: float) -> list[dict[str, Any]]:
        """Wait for the call's closing lines (the agent writes them after the room is gone), then stop."""
        await self.wait_until(lambda _: self.done_seen, timeout_s)
        await self.stop()
        return self.lines

    async def stop(self) -> None:
        if self._proc is not None and self._proc.returncode is None:
            self._proc.kill()
        if self._task is not None:
            self._task.cancel()
        if self._proc is not None:
            await self._proc.wait()


def render(lines: list[dict[str, Any]]) -> list[str]:
    """One readable line each: '2026-10-08T03:00:24 INFO call: message'."""
    out = []
    for o in lines:
        ts = str(o.get("timestamp", ""))[:23]
        out.append(f"{ts} {o.get('level', ''):<7} {o.get('name', '')}: {o.get('message', '')}")
    return out


def sent_texts(lines: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The texts the agent tried to send: {"to", "message", "timestamp"}, oldest first.

    The agent logs `sending_text to=+1... from=+1... message='<body>'` (logger
    tool.external-actions) just before it hands the body to its SMS provider."""
    import ast
    import re

    out = []
    for o in lines:
        msg = str(o.get("message", ""))
        if not msg.startswith("sending_text"):
            continue
        m = re.match(r"sending_text to=(\S+) from=\S+ message=(.*)\Z", msg, re.S)
        if not m:
            continue
        body = m.group(2).strip()
        try:
            body = ast.literal_eval(body)  # the agent logs the body as a Python string literal
        except (ValueError, SyntaxError):
            pass
        out.append({"to": m.group(1), "message": str(body), "timestamp": str(o.get("timestamp", ""))})
    return out


def text_failures(lines: list[dict[str, Any]]) -> list[str]:
    """Why the SMS provider refused a text, one entry per failure the agent logged."""
    import re

    out = []
    for o in lines:
        msg = str(o.get("message", ""))
        if msg.startswith("text_failed") or msg.startswith("sms_send_rejected"):
            m = re.search(r"reason=(.*?)(?: error=|\Z)", msg, re.S)
            out.append((m.group(1) if m else msg[:200]).strip())
    return out


def callback_tasks(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The callback tasks the agent tried to create, oldest first.

    The agent's `request_callback` tool logs `api_call_requested tool=request_callback
    args={'phone_number': ..., 'reason': ...}` (tool.http-request), POSTs to
    `.../locations/<id>/tasks` (http-request: calling_api), and logs the reply as
    `api_responded <url> status=201`. Each entry: {"phone", "reason", "status", "timestamp"};
    status is the HTTP status of the tasks call that followed, or None when no reply was logged."""
    import ast
    import re

    out: list[dict[str, Any]] = []
    for o in lines:
        msg = str(o.get("message", ""))
        if msg.startswith("api_call_requested") and "tool=request_callback" in msg:
            m = re.search(r"args=(\{.*\})\s*\Z", msg, re.S)
            try:
                args = ast.literal_eval(m.group(1)) if m else {}
            except (ValueError, SyntaxError):
                args = {}
            out.append({"phone": str(args.get("phone_number", "")), "reason": str(args.get("reason", "")),
                        "status": None, "timestamp": str(o.get("timestamp", ""))})
        elif out and out[-1]["status"] is None and msg.startswith("api_responded") and "/tasks " in msg + " ":
            m = re.search(r"status=(\d+)", msg)
            if m:
                out[-1]["status"] = int(m.group(1))
    return out


def callback_created(lines: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The latest callback task the task service accepted (HTTP 2xx), or None."""
    done = [t for t in callback_tasks(lines) if t["status"] is not None and 200 <= t["status"] < 300]
    return done[-1] if done else None


def call_record(lines: list[dict[str, Any]]) -> dict[str, Any]:
    """What the agent logged about writing and sending the call's record (logger `call` / `call-log`).

    Keys: turns (transcript turns analysed, None if never logged), fields (the structured fields
    the call analysis extracted), summary_source, analysis (the one-line preview of the extraction the agent logs -
    cut at 160 characters), delivered (HTTP status of the webhook POST, None if not delivered),
    failure (what went wrong, "" if nothing did)."""
    import ast
    import re

    rec: dict[str, Any] = {"turns": None, "fields": [], "summary_source": "", "analysis": "",
                           "delivered": None, "failure": ""}
    for o in lines:
        msg = str(o.get("message", ""))
        if msg.startswith("transcript_analyzed"):
            m = re.search(r"turns=(\d+)", msg)
            if m:
                rec["turns"] = int(m.group(1))
        elif msg.startswith("call_summary source="):
            rec["summary_source"] = msg.split("source=", 1)[1].split()[0]
        elif msg.startswith("structured_output name=call_analysis"):
            # `... name=call_analysis by=openai:gpt-4o-mini fields=['call_summary', ...] in 2805ms raw={...}`
            m = re.search(r"fields=(\[.*?\])", msg)
            try:
                rec["fields"] = list(ast.literal_eval(m.group(1))) if m else []
            except (ValueError, SyntaxError):
                rec["fields"] = []
            m = re.search(r"raw=(.*)\Z", msg, re.S)
            rec["analysis"] = m.group(1) if m else ""
        elif msg.startswith("call_log_delivered"):
            m = re.search(r"status=(\d+)", msg)
            rec["delivered"] = int(m.group(1)) if m else 0
        elif msg.startswith(("call_log_failed", "call_log_validation_failed")):
            rec["failure"] = msg[:200]
    return rec


def last10(phone: str) -> str:
    """The ten digits that identify a US number, however it is written (+1 480-555-0142, 4805550142)."""
    import re

    return re.sub(r"\D", "", phone)[-10:]


def mask(phone: str) -> str:
    """For reports that are published: the last four digits only."""
    digits = last10(phone)
    return f"number ending {digits[-4:]}" if digits else "no number"


def sms_number_problem(sms_phone: str, caller_phone: str) -> str | None:
    """Why SMS_TEST_PHONE cannot be used, or None. Checked before the call is made."""
    import re

    if not sms_phone.strip():
        return ("SMS_TEST_PHONE is not set: put the number that should receive the test text in .env "
                "(and as the SMS_TEST_PHONE repository secret in CI). It must differ from TEST_CALLER_PHONE.")
    if len(re.sub(r"\D", "", sms_phone)) not in (10, 11):
        return "SMS_TEST_PHONE must be a 10-digit number (an optional leading 1 is fine)."
    if last10(sms_phone) == last10(caller_phone):
        return "SMS_TEST_PHONE is the same as the caller's number (TEST_CALLER_PHONE); the text must go to a different one."
    return None


def texts_to(texts: list[dict[str, str]], phone: str) -> list[dict[str, str]]:
    """The sent texts whose destination is `phone`."""
    return [t for t in texts if last10(t["to"]) == last10(phone)]


def redact(text: str, *phones: str) -> str:
    """Replace a number written in any common way (4 8 0 5 5 5..., 480-555-..., +1 (480) ...)
    with its masked form. Used on everything that goes into the published report."""
    import re

    for phone in phones:
        digits = last10(phone)
        if len(digits) == 10:
            pattern = r"(?:\+?1[\s.\-]*)?" + r"[\s.\-—–()]*".join(digits)
            text = re.sub(pattern, f"[{mask(phone)}]", text)
    return text
