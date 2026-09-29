"""
Every test run ends with report/index.html - through make or not (agreed
2026-09-28). The three pytest suites call these two hooks from their conftest:

  default_junit   a run started without --junitxml (a plain `uv run pytest`)
                  still leaves report/data/junit/<suite>.xml, the file the
                  combined report is built from
  build           when pytest exits, rebuild report/index.html

The browser suite does the same from tests/ui/src/reporters/combined-report.ts.

Skipped when there is nothing to report (--collect-only, as `make check-types`
runs it) and when LKQA_NO_REPORT=1, which tools/run_parallel.sh sets so parallel
lanes do not all rebuild at once - it builds once at the end instead.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _wanted(config) -> bool:
    return not (
        config.option.collectonly
        or os.getenv("LKQA_NO_REPORT") == "1"
        or hasattr(config, "workerinput")  # an xdist worker; the controller reports
    )


def default_junit(config, suite: str) -> None:
    if _wanted(config) and not config.option.xmlpath:
        path = ROOT / "report" / "data" / "junit" / f"{suite}.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        config.option.xmlpath = str(path)


def build(config) -> None:
    if not _wanted(config):
        return
    # build_report.py is stdlib only, so any interpreter runs it - this one.
    done = subprocess.run([sys.executable, str(ROOT / "tools" / "build_report.py")], capture_output=True, text=True)
    print("\n" + (done.stdout.strip() or done.stderr.strip()))
