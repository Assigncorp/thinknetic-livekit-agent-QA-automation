"""
The judge's transcript model and oracle, imported rather than copied.

Every other seam in this repo duplicates on purpose (anchors.ts / anchors.py),
and pays for it with a parity test. This one does not, because the thing on the
other side is the VERDICT. Two oracles would mean a call can pass in one suite
and fail in the other with nobody able to say which is right, and
docs/deterministic-kb-testing.md §8 is explicit: one implementation, many
collectors. So the SDK suite puts judge/ on the path and scores with
judge/src/oracle.py itself.

The judge's core is stdlib + python-dotenv - no model SDK, no network - so the
import costs this suite nothing it does not already install.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JUDGE = ROOT / "tests" / "judge"

if str(JUDGE) not in sys.path:
    sys.path.insert(0, str(JUDGE))

from src import anchors, oracle, testbed  # noqa: E402
from src.transcript import Transcript, Turn  # noqa: E402

__all__ = ["ROOT", "anchors", "oracle", "testbed", "Transcript", "Turn"]
