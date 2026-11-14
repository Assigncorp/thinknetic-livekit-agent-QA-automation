"""
Show which environment a run targets and where each of its settings comes from.

    QA_ENV=uat uv run --project tests/sdk python tools/check_env.py

Exits non-zero when a setting the live call needs is missing from the environment's
section of .env, so CI fails before the call instead of skipping it. Secrets are shown
as "set", never printed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "sdk"))

from lkqa import env  # noqa: E402


def main() -> int:
    origin = env.load()
    name, pre = env.name(), env.prefix()
    print(f"== env: {name} (the {pre} section of .env)")
    for key in env.PER_ENV:
        value = os.getenv(key, "")
        shown = "set" if value and key in env.SECRETS else (value or "-")
        where = origin.get(key) or ("process environment" if value else "MISSING" if key in env.REQUIRED else "")
        print(f"   {key:<20} {shown:<45} {where}")
    if missing := env.missing():
        print(f"== env: {len(missing)} setting(s) missing for {name}: set {', '.join(pre + k for k in missing)} "
              f"in .env (in CI: in the ENV_FILE secret)")
        if name not in (found := env.sections()):
            print(f"   .env has no {pre} section; sections found: {', '.join(found) or 'none'}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
