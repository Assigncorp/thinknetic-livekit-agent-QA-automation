"""
Show which environment a run targets and where each of its settings comes from.

    QA_ENV=prod uv run --project tests/sdk python tools/check_env.py

Exits non-zero when a setting the live call needs is missing - from the environment's
section of .env on a laptop, from its repository secrets and variables in CI - so CI fails
before the call instead of skipping it. Secrets are shown as "set", never printed.
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
    ci = env.in_ci()
    where_from = "repository secrets and variables" if ci else ".env"
    print(f"== env: {name} (from {where_from}: " + (f"names starting {pre})" if pre else "names without a prefix)"))
    for key in env.PER_ENV:
        value = os.getenv(key, "")
        shown = "set" if value and key in env.SECRETS else (value or "-")
        source = origin.get(key) or "process environment"
        if ci and source == "process environment":
            source = f"secret or variable {env.setting_name(key)}"
        where = source if value else ("MISSING" if key in env.REQUIRED else "")
        print(f"   {key:<20} {shown:<45} {where}")
    if missing := env.missing():
        print(f"== env: {len(missing)} setting(s) missing for {name}: {env.how_to_set(missing)}")
        if not ci and name not in (found := env.sections()):
            print(f"   .env has no {env.setting_name('LIVEKIT_URL')} line; environments found: {', '.join(found) or 'none'}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
