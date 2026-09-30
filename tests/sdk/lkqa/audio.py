"""
What the agent sounds like, measured rather than listened to.

The agent publishes a microphone track (`roomio_audio`) even when the caller
only types - VERIFIED 2026-09-28 - so every call is also a voice call, and a
turn that reads perfectly in the transcript can still have been silence on the
line. `AgentAudio` samples the track's energy frame by frame so a test can ask
"was anything actually spoken while that turn was on screen?".

`CallerMic` is the other direction: a WAV pushed into a published microphone
track in real time, so the agent's own STT and VAD are what hear the question.
"""

from __future__ import annotations

import asyncio
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

STT_RATE = 16000


@dataclass
class AudioFrameStat:
    t: float  # monotonic seconds, the call's clock
    ms: float
    rms: float


@dataclass
class AgentAudio:
    """Energy timeline of the agent's audio track (and, optionally, the PCM)."""

    silence_rms: float
    keep_pcm: bool = False
    frames: list[AudioFrameStat] = field(default_factory=list)
    _pcm: list[tuple[float, np.ndarray]] = field(default_factory=list)
    _task: asyncio.Task[Any] | None = None

    def attach(self, track: Any) -> None:
        from livekit import rtc

        stream = rtc.AudioStream(track, sample_rate=STT_RATE, num_channels=1)

        async def pump() -> None:
            async for event in stream:
                frame = event.frame
                samples = np.frombuffer(frame.data, dtype=np.int16)
                if samples.size == 0:
                    continue
                now = time.monotonic()
                rms = float(np.sqrt(np.mean((samples.astype(np.float32) / 32768.0) ** 2)))
                self.frames.append(
                    AudioFrameStat(now, 1000 * frame.samples_per_channel / frame.sample_rate, rms)
                )
                if self.keep_pcm:
                    self._pcm.append((now, samples.copy()))

        self._task = asyncio.create_task(pump())

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

    # -- questions a test asks ------------------------------------------

    @property
    def attached(self) -> bool:
        return self._task is not None

    def speech_ms(self, start: float, end: float) -> float:
        return sum(
            f.ms for f in self.frames if start <= f.t <= end and f.rms >= self.silence_rms
        )

    def first_speech_after(self, t: float) -> float | None:
        for f in self.frames:
            if f.t >= t and f.rms >= self.silence_rms:
                return f.t
        return None

    def last_speech_before(self, t: float) -> float | None:
        found = None
        for f in self.frames:
            if f.t > t:
                break
            if f.rms >= self.silence_rms:
                found = f.t
        return found

    def peak_rms(self, start: float, end: float) -> float:
        values = [f.rms for f in self.frames if start <= f.t <= end]
        return max(values) if values else 0.0

    def pcm(self, start: float, end: float) -> np.ndarray:
        """float32 mono 16 kHz between two instants - what whisper wants."""
        chunks = [s for t, s in self._pcm if start <= t <= end]
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks).astype(np.float32) / 32768.0


class CallerMic:
    """A published microphone that plays WAV files into the call."""

    RATE = 48000
    FRAME = 480  # 10 ms

    def __init__(self) -> None:
        self._source: Any = None
        self.track_sid: str | None = None

    async def publish(self, room: Any) -> str:
        from livekit import rtc

        self._source = rtc.AudioSource(self.RATE, 1)
        track = rtc.LocalAudioTrack.create_audio_track("qa-caller-mic", self._source)
        options = rtc.TrackPublishOptions()
        options.source = rtc.TrackSource.SOURCE_MICROPHONE
        publication = await room.local_participant.publish_track(track, options)
        self.track_sid = publication.sid
        return publication.sid

    async def play(self, path: Path, trailing_silence_s: float = 1.5) -> tuple[float, float]:
        """Push the file in real time; returns (speech start, speech end).

        Real time matters: capture_frame only blocks once the source's queue is
        full, so frames are paced against the wall clock here rather than
        dumped - an agent VAD fed ten seconds of audio in one burst hears a
        different utterance from the one a person would say.
        """
        from livekit import rtc

        with wave.open(str(path), "rb") as wav:
            if wav.getframerate() != self.RATE or wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise ValueError(
                    f"{path.name} must be {self.RATE} Hz mono 16-bit - regenerate it with "
                    f"sdk/fixtures/make_fixtures.sh"
                )
            pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)

        silence = np.zeros(int(self.RATE * trailing_silence_s), dtype=np.int16)
        started = time.monotonic()
        speech_end = started + len(pcm) / self.RATE
        for block in (pcm, silence):
            for i in range(0, len(block), self.FRAME):
                chunk = block[i : i + self.FRAME]
                if len(chunk) < self.FRAME:
                    chunk = np.pad(chunk, (0, self.FRAME - len(chunk)))
                frame = rtc.AudioFrame(chunk.tobytes(), self.RATE, 1, self.FRAME)
                await self._source.capture_frame(frame)
                due = started + (i + self.FRAME) / self.RATE + (0 if block is pcm else len(pcm) / self.RATE)
                delay = due - time.monotonic()
                if delay > 0:
                    await asyncio.sleep(delay)
        return started, speech_end
