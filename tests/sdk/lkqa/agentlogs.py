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

# The agent writes this once the call is over and its record is saved.
CALL_DONE = ("call_log_delivered", "voice_session_closed")


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


async def fetch(room: str, *, quiet_s: float = 4, deadline_s: float = 90) -> list[dict[str, Any]]:
    """Every worker log line for `room`, oldest first."""
    aid = await agent_id()
    proc = await asyncio.create_subprocess_exec(
        "lk", "agent", "logs", "--id", aid,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    lines: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    stop_at = loop.time() + deadline_s
    done_seen_at: float | None = None
    try:
        assert proc.stdout is not None
        while loop.time() < stop_at:
            try:
                raw = await asyncio.wait_for(proc.stdout.readline(), quiet_s)
            except asyncio.TimeoutError:
                # Quiet. If the call has finished, that is everything; otherwise keep waiting.
                if done_seen_at is not None:
                    break
                continue
            if not raw:
                break
            obj = parse(raw.decode("utf-8", "replace"))
            if obj and obj.get("room") == room:
                lines.append(obj)
                if any(k in str(obj.get("message", "")) for k in CALL_DONE) and done_seen_at is None:
                    done_seen_at = loop.time()
    finally:
        if proc.returncode is None:
            proc.kill()
        await proc.wait()
    return lines


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
