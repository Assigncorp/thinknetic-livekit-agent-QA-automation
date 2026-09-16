# Front door for both toolchains. Run everything from the repo root.
SHELL := /bin/bash

.PHONY: help check install install-ui install-api smoke ui api voice negative test report clean

help:
	@echo "make check       - verify the local toolchain and .env"
	@echo "make install     - install UI (pnpm/npm + chromium) and API (uv) dependencies"
	@echo "make smoke       - fast page-load + critical-element checks"
	@echo "make ui          - full Playwright functional suite"
	@echo "make negative    - negative / fail-closed suite only"
	@echo "make api         - Python API suite against the public endpoints"
	@echo "make voice       - LiveKit voice suite (phase 3, currently skipped)"
	@echo "make test        - api + ui"
	@echo "make report      - open the last Playwright HTML report"
	@echo "make clean       - remove test output"

check:
	@./scripts/check-env.sh

install: install-ui install-api

install-ui:
	cd ui && (command -v pnpm >/dev/null && pnpm install || npm install)
	cd ui && npx playwright install chromium

install-api:
	cd api && uv sync

smoke:
	cd ui && npx playwright test tests/smoke

ui:
	cd ui && npx playwright test

negative:
	cd ui && npx playwright test tests/negative

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
