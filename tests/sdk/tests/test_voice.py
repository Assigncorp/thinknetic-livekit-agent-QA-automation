"""
VOI / TRN-10: the call as a voice caller experiences it.

One spoken call carries VOI-01..05: the caller's question is a WAV pushed into a
published microphone track, so the agent's own VAD and STT are what hear it; the
agent's audio is sampled frame by frame, and (with the `stt` extra) transcribed
locally to check it said what it wrote. Barge-in gets a session of its own,
because interrupting the agent changes the rest of that call.
"""

from __future__ import annotations

import asyncio
import re

import pytest

from conftest import gate
from lkqa import cases
from lkqa.bridge import ROOT, testbed
from lkqa.call import AgentHungUp, Call
from lkqa.driver import ScoredCall, scored_call, timings
from lkqa.session import request_session

pytestmark = [pytest.mark.live, pytest.mark.voice]

SDK = testbed.config()["livekitSdk"]
SPOKEN = SDK["spokenQuestion"]


@pytest.fixture(scope="module")
async def spoken_call(report, r) -> ScoredCall:
    scenario = testbed.scenario_by_id(SPOKEN["scenarioId"])
    return await scored_call(
        report, "voice", scenario, cases.serial_for(scenario["kbId"], r), r,
        question=SPOKEN["text"], ask_as="voice", keep_pcm=True,
        # An FAQ: ask for the value, never push for "the full troubleshooting
        # steps" - VERIFIED 2026-09-28 that push produced a non-KB procedure
        # whose 3,000 PSI gauge was then judged as the answer.
        mode="faq" if scenario.get("kind") == "faq" else "default",
    )


def test_voi01_the_agent_speaks_within_budget_of_connecting(spoken_call):
    call = spoken_call.call
    first = call.audio.first_speech_after(call.t0)
    assert first is not None, "the agent's audio track never carried anything above silence"
    assert call.ms(first) <= int(SDK["budgets"]["firstAgentAudioMs"]), f"first audible speech at {call.ms(first)}ms"


def test_voi02_every_agent_turn_was_actually_spoken(spoken_call, report):
    """A turn that reads perfectly and was silence on the line is a TTS failure
    no transcript-based test can see."""
    call = spoken_call.call
    floor = float(SDK["audio"]["minSpeechMsPerTurn"])
    per_turn = []
    for s in call.agent_segments(include_idle=True):
        speech = call.audio.speech_ms(s.opened - 0.5, s.closed + 0.5)
        per_turn.append({"text": s.text[:60], "speechMs": int(speech), "peakRms": round(call.audio.peak_rms(s.opened, s.closed), 4)})
    report.record("VOI-02", turns=per_turn)
    silent = [t for t in per_turn if t["speechMs"] < floor]
    assert not silent, f"turns with under {floor}ms of audible speech: {silent}"


def test_voi03_the_line_is_quiet_while_the_agent_is_listening(spoken_call, report):
    """No phantom audio - a hot line while 'listening' is the agent talking over
    a caller it believes it is waiting for."""
    call = spoken_call.call
    windows = []
    states = call.states + [(call.disconnected_at or call.states[-1][0], "end")]
    for (t, s), (t_next, _) in zip(states, states[1:]):
        if s == "listening" and t_next - t > 2.5:
            windows.append((t + 0.8, t_next - 0.2))  # skip the TTS tail and the next onset
    leaked = [(call.ms(a), call.ms(b), int(call.audio.speech_ms(a, b))) for a, b in windows]
    report.record("VOI-03", listeningWindows=leaked)
    noisy = [w for w in leaked if w[2] > 300]
    assert not noisy, f"audible audio while listening (startMs, endMs, speechMs): {noisy}"


def test_voi04_the_spoken_question_is_heard_and_answered_from_the_manual(spoken_call):
    """The agent's STT heard the question (its caller transcription carries the
    key words) and the answer passes the oracle's zero-tolerance checks."""
    heard = " ".join(s.text for s in spoken_call.call.caller_transcriptions()).lower()
    key = [w for w in re.findall(r"[a-z]+", SPOKEN["text"].lower()) if len(w) > 3]
    if heard:
        missing = [w for w in key if w not in heard]
        assert len(missing) <= 1, f"the agent heard {heard!r}; missing {missing}"
    assert spoken_call.grounding.applicable, f"no scoreable answer to the spoken question:\n{spoken_call.dialogue()}"
    assert not spoken_call.grounding.zero_tolerance_failures, "\n".join(spoken_call.grounding.zero_tolerance_failures)


def test_voi04b_the_agent_transcribes_the_callers_speech(spoken_call, report):
    """Recorded separately: whether the agent publishes the CALLER's transcript
    is a deployment choice; the answer above already proves it heard us."""
    heard = [s.text for s in spoken_call.call.caller_transcriptions()]
    report.record("VOI-04b", callerTranscriptions=heard)
    if not heard:
        report.finding("VOI-04b", "the agent does not publish the caller's speech transcription on lk.transcription")


def test_voi05_what_the_agent_says_is_what_it_writes(spoken_call, report):
    """Local STT of the agent's audio against its own transcription, per turn.

    Two comparisons, because they fail differently:
      * MEASUREMENTS - the figures heard must be the figures written. Parsed on
        both sides with the oracle's numerals grammar, so "2000 psi" (whisper)
        and "two thousand PSI" (transcript) are the same fact. A mismatch here
        is a caller hearing a different number from the one on screen.
      * WORDS - recall of the non-numeric content words, a coarse TTS check.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        pytest.skip("faster-whisper not installed - cd tests/sdk && uv sync --extra stt")
    from src import numerals

    model = WhisperModel(SDK["stt"]["model"], device="cpu", compute_type="int8")
    call = spoken_call.call
    results = []
    for s in call.agent_segments():
        pcm = call.audio.pcm(s.opened - 0.5, s.closed + 1.0)
        if pcm.size < 16000:
            continue
        heard = " ".join(seg.text for seg in model.transcribe(pcm, language="en", beam_size=1)[0]).strip()
        written_figures = sorted({numerals.key_of(m) for m in numerals.extract(s.text)})
        heard_figures = sorted({numerals.key_of(m) for m in numerals.extract(heard)})
        results.append({
            "written": s.text, "spoken": heard, "recall": _recall(s.text, heard),
            "writtenFigures": written_figures, "spokenFigures": heard_figures,
            "missingFigures": sorted(set(written_figures) - set(heard_figures)),
        })
    report.record("VOI-05", turns=results)
    assert results, "no agent turn had enough captured audio to transcribe"

    wrong_figures = [r for r in results if r["missingFigures"]]
    floor = float(SDK["stt"]["minWordRecall"])
    low = [r for r in results if r["recall"] < floor]
    if wrong_figures or low:
        if gate("audioTextConsistency"):
            pytest.fail(f"spoken audio diverges from the transcript: figures {wrong_figures}, words {low}")
        if wrong_figures:
            report.finding("VOI-05", "a figure in the transcript was not heard in the audio", turns=wrong_figures)
        if low:
            report.finding("VOI-05", f"{len(low)} turn(s) with word recall < {floor}", turns=low)


_NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
    "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
    "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "point",
}


def _words(text: str) -> list[str]:
    stop = {"the", "a", "an", "and", "or", "to", "of", "is", "it", "you", "your", "i", "for", "on", "in", "that", "this", "be"}
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in stop and w not in _NUMBER_WORDS]


def _recall(written: str, heard: str) -> float:
    want = _words(written)
    got = set(_words(heard))
    return round(sum(1 for w in want if w in got) / len(want), 3) if want else 1.0


async def test_trn10_barge_in_stops_the_agent(report, r):
    """TRN-10. The caller talks over a long answer; the agent should stop
    speaking. Report-only (livekitSdk.gates.bargeIn) until a baseline exists.

    Interrupts the FIRST answer to a walkthrough question - the longest turn
    this agent produces - rather than holding a whole conversation first, by
    which point the agent may already have wrapped up."""
    scenario = testbed.scenario_by_id(SDK["grounding"]["pinned"][0])
    grant = request_session(cases.caller(r, cases.serial_for(scenario["kbId"], r)))
    async with Call(grant) as call:
        await call.settle(timeout_ms=int(testbed.config()["budgets"]["machineIdentifiedMs"]), drain=True)
        asked_at = await call.say(scenario["question"])
        speaking = await call.wait_for_state({"speaking"}, int(testbed.config()["budgets"]["answerMs"]), after=asked_at)
        if speaking is None:
            pytest.skip("the agent never started answering, so there was nothing to interrupt")
        await asyncio.sleep(2.0)
        was_speaking = call.state == "speaking"
        start, _ = await call.speak(ROOT / SPOKEN["bargeInWav"], text=SPOKEN["bargeInText"], wait=False)
        stopped = await call.wait_for_state({"listening", "thinking"}, 10000, after=start)
        await asyncio.sleep(3)
        last_audio = call.audio.last_speech_before(start + 3)
    ms = None if stopped is None else int((stopped - start) * 1000)
    audio_ms = None if last_audio is None else int((last_audio - start) * 1000)
    report.record("TRN-10", stillSpeakingAtInterrupt=was_speaking, bargeInStateChangeMs=ms,
                  agentAudioUntilMsAfterInterrupt=audio_ms, timings=timings(call))
    if not was_speaking:
        pytest.skip("the agent finished its turn before the interruption landed")
    budget = int(SDK["budgets"]["bargeInStopMs"])
    if ms is None or ms > budget:
        if gate("bargeIn"):
            pytest.fail(f"agent kept speaking {ms}ms after the caller interrupted (budget {budget}ms)")
        report.finding("TRN-10", f"barge-in: agent state changed {ms}ms after the caller started speaking (budget {budget}ms)")
