# Front door for both toolchains. Run everything from the repo root.
SHELL := /bin/bash

.PHONY: help check install install-ui install-api install-tools resources \
        smoke regression negative catalog ui chat demo api voice test report clean

help:
	@echo "make check       - verify the local toolchain and .env"
	@echo "make install     - install UI (npm + chromium), API and tools dependencies"
	@echo "make resources   - rebuild resources/generated from config + KB files + workbook"
	@echo ""
	@echo "Test categories (see docs/test-plan.md):"
	@echo "make catalog     - scenario catalogue checks (no browser, no agent calls, <1s)"
	@echo "make api         - public endpoint suite + catalogue"
	@echo "make smoke       - @smoke      fast page-load + critical-element checks"
	@echo "make regression  - @regression product content + session lifecycle"
	@echo "make negative    - @negative   bad routes / fail-closed behaviour"
	@echo "make chat        - @chat       the real agent chat flow (opens live sessions)"
	@echo "make ui          - full browser suite EXCEPT tests that open a real session"
	@echo "make demo        - ONE live chat session, visible browser, ~90s"
	@echo "make test        - api + ui  (no live sessions)"
	@echo ""
	@echo "make report      - open the last Playwright HTML report"
	@echo "make clean       - remove test output"

check:
	@./scripts/check-env.sh

install: install-ui install-api install-tools

install-ui:
	cd ui && (command -v pnpm >/dev/null && pnpm install || npm install)
	cd ui && npx playwright install chromium

install-api:
	cd api && uv sync

install-tools:
	cd tools && uv sync

# Rebuild serial-index.json and scenarios.json from config/testbed.config.json.
# Run after renaming a KB file, adding a machine, or updating the workbook.
resources:
	cd tools && uv run python build_resources.py

catalog:
	cd api && uv run pytest tests/test_scenario_catalog.py -q

smoke:
	cd ui && npx playwright test --grep @smoke

regression:
	cd ui && npx playwright test --grep @regression

negative:
	cd ui && npx playwright test --grep @negative

# Everything that does not open a real agent session.
ui:
	cd ui && npx playwright test --grep-invert @live

# The real thing: opens sessions against the dev deployment.
chat:
	cd ui && npx playwright test --grep @chat

# DEMO: one live chat session, visible browser, one worker, readable output.
# The full positive path only - roughly 60-90 seconds.
demo:
	cd ui && npx playwright test -g "full positive workflow" --headed --workers 1 --reporter=list

api:
	cd api && uv run pytest -v

voice:
	cd voice && uv run pytest -v

test: api ui

report:
	cd ui && npx playwright show-report

clean:
	rm -rf ui/test-results ui/playwright-report ui/blob-report reports/* voice/recordings
	@touch reports/.gitkeep
