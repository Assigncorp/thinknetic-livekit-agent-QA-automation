"""
One scored call: session -> conversation -> recording -> oracle verdict.

Every grounding, trap and voice test is this function with a different question,
so they differ only in what they ask and what they assert.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import cases, grounding
from .bridge import Transcript
from .call import AgentHungUp, Call, Step
from .report import Report
from .session import Grant, request_session


@dataclass
class ScoredCall:
    call: Call
    grant: Grant
    steps: list[Step]
    wrap: list[Step]
    transcript: Transcript
    grounding: grounding.Grounding
    recording: Path

    def dialogue(self) -> str:
        lines = []
        for t in self.transcript.turns:
            who = "AGENT " if t.speaker == "agent" else "CALLER"
            tag = f" [{t.intent}]" if t.intent else ""
            lines.append(f"  {who}{tag}: {t.text}")
        return "\n".join(lines)


def timings(call: Call) -> dict[str, Any]:
    agent = call.agent_segments()
    return {
        "agentJoinMs": call.ms(call.agent_joined_at),
        "agentAudioTrackMs": call.ms(call.agent_audio_track_at),
        "firstAgentSpeechMs": call.ms(call.audio.first_speech_after(call.t0)) if call.audio.attached else None,
        "firstTurnMs": call.ms(agent[0].closed) if agent else None,
        "turnMs": [int((s.closed - s.opened) * 1000) for s in agent],
        "states": [(call.ms(t), s) for t, s in call.states],
    }


async def scored_call(
    report: Report,
    label: str,
    scenario: dict[str, Any],
    serial: str,
    r: random.Random,
    *,
    question: str | None = None,
    planted: str | None = None,
    probe: str | None = None,
    ask_as: str = "text",
    keep_pcm: bool = False,
    wrap_up: bool = False,
    caller: dict[str, str] | None = None,
    section_scenario: dict[str, Any] | None = None,
    mode: str = "default",
) -> ScoredCall:
    asked = question or scenario["question"]
    grant = request_session(caller or cases.caller(r, serial))
    call = Call(grant, keep_pcm=keep_pcm)
    started = time.monotonic()
    print(f"\n[lkqa] {label}: {scenario.get('id', 'adhoc')} on {serial} ({scenario.get('kbId') or 'no KB'}) room={grant.room}")
    steps: list[Step] = []
    wrap: list[Step] = []
    try:
        await call.connect()
        try:
            steps = await call.converse(asked, ask_as=ask_as, mode=mode)
        except AgentHungUp as exc:
            steps.append(Step("agentHungUp", str(exc), None, 0))
        if wrap_up and not call.agent_gone:
            wrap = await call.wrap_up()
    finally:
        await call.hang_up()
        # Saved even when the call blew up: a failure with no transcript
        # behind it cannot be diagnosed, and it cannot be re-run either.
        transcript = call.to_transcript({**scenario, "question": asked})
        path = report.save_transcript(transcript, label)
        print(f"[lkqa] recording: report/data/recordings/{path.name}")

    verdict = grounding.evaluate(transcript, planted, probe, section_scenario)
    scored = ScoredCall(call, grant, steps, wrap, transcript, verdict, path)

    print(scored.dialogue())
    print("[lkqa] oracle verdict:\n" + verdict.explain())
    report.record(
        label,
        scenario=scenario.get("id"),
        kb=scenario.get("kbId"),
        serial=serial,
        room=grant.room,
        question=asked,
        probeType=probe,
        recording=str(path.name),
        durationMs=int((time.monotonic() - started) * 1000),
        steps=[{"intent": s.intent, "waitedMs": s.waited_ms, "reply": s.reply} for s in steps + wrap],
        grounding=verdict.summary(),
        timings=timings(call),
    )
    return scored
