"""
PLACEHOLDER - LiveKit session tests (phase 3).

Skipped wholesale until credentials are wired. The shape below is the intended
contract, not working code: keep it honest by leaving it skipped rather than
letting a hollow test report green.
"""

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("LIVEKIT_URL"),
    reason="LIVEKIT_URL not set - voice suite not yet enabled",
)


def test_agent_joins_room():
    """Join a room, assert the agent participant appears within budget."""
    pytest.skip("not implemented - phase 3")


def test_agent_responds_to_published_audio():
    """Publish a caller WAV, assert an audio track comes back."""
    pytest.skip("not implemented - phase 3")


def test_first_response_latency_within_budget():
    """End-of-user-speech to first agent audio frame."""
    pytest.skip("not implemented - phase 3")
