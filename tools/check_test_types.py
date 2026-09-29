"""
`make check-types`: every browser test carries exactly one testing type tag.

The Python suites enforce the same rule at collection time (TEST_TYPES_STRICT=1
in their conftests). Playwright has no such hook, so this reads its own JSON
test listing - `npx playwright test --list --reporter=json` - on stdin.
"""

import json
import sys

# Playwright's JSON reports tags without the "@", already merged from describe().
TYPES = {"positive", "negative", "edge", "security", "nonfunctional"}


def walk(suite, inherited, out):
    tags = inherited | set(suite.get("tags") or [])
    for spec in suite.get("specs", []):
        spec_tags = tags | set(spec.get("tags") or [])
        for test in spec.get("tests", []) or [None]:
            found = sorted(spec_tags & TYPES)
            out.append((f"{spec.get('file')}:{spec.get('line')} {spec['title']}", found))
    for child in suite.get("suites", []):
        walk(child, tags, out)


listing = json.load(sys.stdin)
results = []
for suite in listing.get("suites", []):
    walk(suite, set(), results)
bad = [(t, f) for t, f in results if len(f) != 1]
if bad:
    print("browser tests without exactly one testing type tag:")
    for title, found in bad:
        print(f"  {found or 'none'}  {title}")
    sys.exit(1)
print(f"browser: all {len(results)} tests carry exactly one testing type")
