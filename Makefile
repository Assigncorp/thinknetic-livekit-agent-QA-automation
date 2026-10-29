SHELL := /bin/bash
export PYTHONDONTWRITEBYTECODE := 1

SDK := tests/sdk
PY := uv run --project $(SDK) python

# The environment the live call targets: its section of .env (SIT_..., UAT_..., PROD_...).
export QA_ENV ?= sit

.PHONY: help smoke test install clean check-env unit kb report bank-draft check-bank

help:
	@echo "make smoke       - the whole smoke run, same steps as CI: clean, install, check-env, unit, kb, report"
	@echo "make test        - check-env, unit, kb, report (no clean/install)"
	@echo "make check-env   - show the environment's settings and where each comes from; fails if one is missing"
	@echo "make unit        - routing + validator + question bank checks (offline); results go to report-internal/"
	@echo "make kb          - the live LiveKit KB-steps call (KB_SEED / KB_MODEL / KB_QUESTION_ID / KB_IMAGE to pin)"
	@echo "make report      - build report/index.html (management) and report-internal/index.html (unit checks)"
	@echo "make bank-draft  - regenerate kb/question_bank.draft.yaml from the KBs"
	@echo "make check-bank  - check kb/question_bank.yaml against the KBs"
	@echo ""
	@echo "QA_ENV picks the environment (default sit): QA_ENV=uat make smoke. Each has its own section in .env."

# The sequence. A missing setting or a unit failure stops the run before the live call;
# the report is always built, pass or fail, and the exit code is the run's verdict.
smoke:
	@export SMOKE_STARTED_AT=$$(date -u +%Y-%m-%dT%H:%M:%SZ); status=0; \
	$(MAKE) --no-print-directory clean && $(MAKE) --no-print-directory install \
		&& $(MAKE) --no-print-directory check-env || status=1; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory unit || status=1; fi; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory kb || status=1; fi; \
	$(MAKE) --no-print-directory report; \
	if [ $$status -eq 0 ]; then echo "== smoke PASSED"; else echo "== smoke FAILED"; fi; exit $$status

test:
	@export SMOKE_STARTED_AT=$$(date -u +%Y-%m-%dT%H:%M:%SZ); status=0; \
	$(MAKE) --no-print-directory check-env || status=1; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory unit || status=1; fi; \
	if [ $$status -eq 0 ]; then $(MAKE) --no-print-directory kb || status=1; fi; \
	$(MAKE) --no-print-directory report; exit $$status

clean:
	@rm -rf report report-internal; \
	find . -type d \( -name __pycache__ -o -name .pytest_cache \) -not -path "*/.venv/*" -prune -exec rm -rf {} + 2>/dev/null; \
	mkdir -p report/data; echo "== clean: previous report and caches removed"

install:
	cd $(SDK) && uv sync

check-env:
	@$(PY) tools/check_env.py

unit:
	@echo "== unit: routing, validator, question bank"
	@mkdir -p report-internal
	cd $(SDK) && uv run pytest -m offline --junitxml=../../report-internal/junit-unit.xml

kb:
	@echo "== kb: live LiveKit KB-steps call on $(QA_ENV)"
	@mkdir -p report/data
	cd $(SDK) && uv run pytest -m live --junitxml=../../report/data/junit-kb.xml

report:
	@$(PY) tools/build_report.py

bank-draft:
	$(PY) tools/build_question_bank.py --report
	$(PY) tools/build_question_bank.py

check-bank:
	$(PY) tools/check_question_bank.py
