SHELL := /bin/bash
export PYTHONDONTWRITEBYTECODE := 1

SDK := tests/sdk
PY := uv run --project $(SDK) python

.PHONY: help smoke test install clean unit kb report bank-draft check-bank

help:
	@echo "make smoke       - the whole smoke run, same steps as CI: clean, install, unit, kb, report"
	@echo "make test        - unit, kb, report (no clean/install)"
	@echo "make unit        - routing + validator + question bank checks (offline); results go to report-internal/"
	@echo "make kb          - the live LiveKit KB-steps call (KB_SEED / KB_MODEL / KB_QUESTION_ID to pin)"
	@echo "make report      - build report/index.html (management) and report-internal/index.html (unit checks)"
	@echo "make bank-draft  - regenerate kb/question_bank.draft.yaml from the KBs"
	@echo "make check-bank  - check kb/question_bank.yaml against the KBs"

# The sequence. A unit failure stops the run before the live call; the
# report is always built, pass or fail, and the exit code is the run's verdict.
smoke:
	@export SMOKE_STARTED_AT=$$(date -u +%Y-%m-%dT%H:%M:%SZ); status=0; \
	$(MAKE) --no-print-directory clean && $(MAKE) --no-print-directory install || status=1; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory unit || status=1; fi; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory kb || status=1; fi; \
	$(MAKE) --no-print-directory report; \
	if [ $$status -eq 0 ]; then echo "== smoke PASSED"; else echo "== smoke FAILED"; fi; exit $$status

test:
	@export SMOKE_STARTED_AT=$$(date -u +%Y-%m-%dT%H:%M:%SZ); status=0; \
	$(MAKE) --no-print-directory unit || status=1; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory kb || status=1; fi; \
	$(MAKE) --no-print-directory report; exit $$status

clean:
	@find report -mindepth 1 ! -name .gitkeep -exec rm -rf {} + 2>/dev/null; \
	rm -rf report-internal; \
	find . -type d \( -name __pycache__ -o -name .pytest_cache \) -not -path "*/.venv/*" -prune -exec rm -rf {} + 2>/dev/null; \
	mkdir -p report/data; echo "== clean: previous report and caches removed"

install:
	cd $(SDK) && uv sync

unit:
	@echo "== unit: routing, validator, question bank"
	@mkdir -p report-internal
	cd $(SDK) && uv run pytest -m offline --junitxml=../../report-internal/junit-unit.xml

kb:
	@echo "== kb: live LiveKit KB-steps call"
	@mkdir -p report/data
	cd $(SDK) && uv run pytest -m live --junitxml=../../report/data/junit-kb.xml

report:
	@$(PY) tools/build_report.py

bank-draft:
	$(PY) tools/build_question_bank.py --report
	$(PY) tools/build_question_bank.py

check-bank:
	$(PY) tools/check_question_bank.py
