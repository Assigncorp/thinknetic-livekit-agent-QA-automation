"""The image request: the one image kb/smoke.yaml names, and how the agent's share is matched to it. Offline."""

from __future__ import annotations

import pytest

from lkqa import kbcall, smoke
from lkqa.kbcall import _same_image

pytestmark = pytest.mark.offline


@pytest.fixture(autouse=True)
def no_pins(monkeypatch):
    for name in ("KB_SEED", "KB_MODEL"):
        monkeypatch.delenv(name, raising=False)


def test_every_call_asks_for_the_one_image_in_the_file(monkeypatch):
    image = smoke.load().image
    assert image.strip()
    assert {smoke.choose(seed).image for seed in range(20)} == {image}
    monkeypatch.setenv("KB_MODEL", "VHRS28")
    assert smoke.choose(1).image == image


def test_received_image_matches_on_description():
    wanted = "Pressure over-ride (POR) adjustment"
    assert _same_image("pressure over-ride (POR) adjustment ", wanted)
    assert not _same_image("Charge pressure adjustment", wanted)
    assert not _same_image("", wanted)


# The "image shown" check, run on recorded log lines and a stand-in for the caller's screen.

class _Screen:
    """The bits of lkqa.call.Call the image check uses: the clock and what reached the screen."""
    def __init__(self, images=()):
        self.images = list(images)

    def _now(self):
        return 0

    def ms(self, _):
        return 0


class _Logs:
    def __init__(self, messages):
        self.lines = [{"message": m, "timestamp": "2026-11-13T09:00:00+00:00"} for m in messages]

    async def wait_until(self, predicate, timeout_s):
        return predicate(self.lines)


def _triggered(messages, received=()):
    attempt = kbcall.Attempt(1)
    flow = kbcall._Flow(_Screen(received), attempt)
    flow.tail = _Logs(messages)
    return flow, attempt.checkpoints["image_triggered"]


SEARCH_NOTHING = ["searching_images kb_id=k scope={} query='joystick calibration'",
                  "image_search candidates=0 with_url=0 cutoff=0.50 query='joystick calibration' | -"]
PUSH = ["searching_images kb_id=k scope={} query='operator console'",
        "pushing_images to=qa-caller-1 images=1 chat_id=None bytes=410", "images_delivered ack=ok"]


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(kbcall, "IMAGE_LOG_WAIT_S", 0)
    monkeypatch.setattr(kbcall, "IMAGE_RECEIVE_WAIT_S", 0)


async def test_no_image_for_the_topic_fails_and_is_never_skipped(quick):
    flow, cp = _triggered(SEARCH_NOTHING)
    await kbcall._check_image_triggered(flow)
    assert (cp.passed, cp.optional) == (False, False)
    assert "found no image for this topic" in cp.detail
    assert not flow.attempt.passed


async def test_a_push_the_screen_never_received_fails(quick):
    flow, cp = _triggered(PUSH)
    await kbcall._check_image_triggered(flow)
    assert cp.passed is False
    assert "received none" in cp.detail


async def test_a_push_the_screen_received_passes(quick):
    flow, cp = _triggered(PUSH, received=[{"description": "Operator control panel or console", "urls": []}])
    await kbcall._check_image_triggered(flow)
    assert cp.passed is True
    assert '"Operator control panel or console"' in cp.detail
