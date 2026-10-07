# Front door for both toolchains. Run everything from the repo root.
SHELL := /bin/bash

TEST_TYPES := positive negative edge security nonfunctional


# ---------------------------------------------------------------------------
# Every run starts from nothing (product owner, 2026-09-28): the FIRST make
# command you type deletes all previous output and every cache in the project -
# report/data/, ui/test-results, __pycache__, .pytest_cache. Nested makes (make all,
# make test-type) skip it, so a run never wipes its own earlier steps. Kept:
# .venv/ and node_modules/ (installed dependencies, not caches), the tracked
# inputs in resources/ and the synthetic fixtures in judge/recordings/.
# Read-only commands (report*, *-rescore, *-report) never depend on it.
# FRESH=0 keeps the previous results for one run.
# ---------------------------------------------------------------------------
export PYTHONDONTWRITEBYTECODE := 1

fresh:
	@if [ "$(MAKELEVEL)" = "0" ] && [ "$(FRESH)" != "0" ]; then \
	  find report -mindepth 1 ! -name .gitkeep -exec rm -rf {} + 2>/dev/null; \
	  rm -rf tests/ui/test-results tests/ui/playwright-report tests/ui/blob-report; \
	  find . -type d \( -name __pycache__ -o -name .pytest_cache \) -not -path "*/node_modules/*" -not -path "*/.venv/*" -prune -exec rm -rf {} + 2>/dev/null; \
	  mkdir -p report/data/junit; \
	  echo "fresh run: previous reports and caches removed"; \
	fi

# Every pytest target leaves report/data/junit/<target>.xml for the combined report.
JUNIT = --junitxml=$(CURDIR)/report/data/junit/$@.xml

.PHONY: fresh help setup check install install-ui install-api install-tools install-judge install-sdk resources \
        livekit livekit-offline livekit-contract livekit-auth livekit-conversation livekit-grounding \
        report-html report-all report-share all test-type check-types $(addprefix test-,$(TEST_TYPES)) \
        livekit-voice livekit-resilience livekit-concurrency livekit-browser livekit-phrasing livekit-report livekit-sdk all-parallel live-parallel ui-live-headed ui-all live-headed demo-livekit livekit-kb livekit-kb-rescore livekit-interview livekit-interview-rescore llm-check \
        smoke regression negative catalog ui chat demo api voice test report clean \
        ratelimit perf perf-report saturate judge judge-offline judge-report \
        oracle oracle-offline oracle-report probe-agent

help:
	@echo "make check       - verify the local toolchain and .env"
	@echo "make install     - install UI (npm + chromium), API and tools dependencies"
	@echo "make resources   - rebuild resources/generated from config + KB files + workbook"
	@echo ""
	@echo "By testing type, across ALL suites (config/test-types.json; live calls included):"
	@echo "make test-type TYPE=negative  - one type: positive | negative | edge | security | nonfunctional"
	@echo "make test-positive / test-negative / test-edge / test-security / test-nonfunctional"
	@echo "make check-types              - every test in every suite has exactly one type"
	@echo ""
	@echo "Test categories (see docs/test-plan.md):"
	@echo "make catalog     - scenario catalogue checks (no browser, no agent calls, <1s)"
	@echo "make api         - public endpoint suite + catalogue"
	@echo "make ratelimit   - @ratelimit rate-limiter contract (~12 requests, safe on a PR)"
	@echo "make perf        - @perf      latency + payload budgets, writes report/data/api-perf.json"
	@echo "make saturate    - @load      DELIBERATELY empties the rate-limit window (~2 min, opt-in)"
	@echo "make smoke       - @smoke      fast page-load + critical-element checks"
	@echo "make regression  - @regression product content + session lifecycle"
	@echo "make negative    - @negative   bad routes / fail-closed behaviour"
	@echo "make chat        - @chat       the real agent chat flow (opens live sessions)"
	@echo "make ui          - full browser suite EXCEPT tests that open a real session"
	@echo "make demo        - ONE live chat session, visible browser, ~90s"
	@echo ""
	@echo "Deterministic KB oracle (judge/src/oracle.py - see docs/deterministic-kb-testing.md):"
	@echo "make oracle-offline - the oracle's own regression suite: grammar, index, applicability"
	@echo "make oracle        - score every recorded call against the compiled KB index (offline)"
	@echo "make oracle-report - show the last report/data/oracle-verdicts.json"
	@echo ""
	@echo "Semantic scoring (judge/ - reports, does not gate; see docs/architecture.md):"
	@echo "make judge-offline - rubric + KB-grounding validation, no network, no account"
	@echo "make judge         - score recorded calls against their KB (needs ANTHROPIC_API_KEY)"
	@echo "make probe-agent   - ask the deployment what its agent worker is called (run FIRST)"
	@echo "make judge-report  - show the last report/data/judge-scores.json"
	@echo ""
	@echo "LiveKit SDK suite (sdk/ - joins real calls with no browser; see docs/livekit-sdk-testing.md):"
	@echo "make livekit-offline     - traps, fixtures and verdict path, no network (<1s, gates a PR)"
	@echo "make livekit-contract    - session endpoint: token grants, dispatch, validation (no agent started)"
	@echo "make livekit-auth        - forged / expired / wrong-secret tokens refused (needs LIVEKIT_*)"
	@echo "make livekit-conversation- one full call: join, greet, route, answer, wrap up, room closes"
	@echo "make livekit-grounding   - IS THE ANSWER FROM THE KB? oracle-scored calls, all machines + traps"
	@echo "make livekit-kb          - EVERY KB FAQ + procedures on live calls, each value judged (~48 calls)"
	@echo "make livekit-kb-rescore  - re-judge the last KB run from its recordings (no calls)"
	@echo "make livekit-interview   - LLM-written KB follow-up questions on live calls, LLM + oracle judged"
	@echo "make llm-check           - is the free LLM key set and the model available?"
	@echo "make livekit-voice       - spoken question in, agent audio measured + transcribed locally"
	@echo "make livekit-resilience  - unknown serial, mid-stream send, idle caller, returning caller"
	@echo "make livekit-concurrency - 3 parallel callers on 3 machines, no cross-talk"
	@echo "make livekit-browser     - Playwright: the page's call as the LiveKit server sees it"
	@echo "make livekit             - all of the above (~25 live sessions, ~35 min)"
	@echo "make livekit-report      - show the last report/data/livekit-sdk.json"
	@echo "make demo-livekit        - DEMO: one grounded call over the SDK, dialogue + oracle verdict live"
	@echo "make test        - api + ui  (no live sessions)"
	@echo ""
	@echo "make all         - EVERYTHING in order, then the combined HTML report (~2h, live calls)"
	@echo "make report-all  - build + open report/index.html (every suite in one page)"
	@echo "make report-html - build report/index.html only"
	@echo "make report      - open the last Playwright HTML report"
	@echo "make clean       - remove test output"

check:
	@./tools/check-env.sh

# ---------------------------------------------------------------------------
# By testing type. Each test in each suite has exactly one type - pytest markers
# from config/test-types.json in api/ judge/ sdk/, Playwright tags in ui/.
# Runs every suite even if an earlier one fails, then reports each exit code.
# Live agent calls ARE included (agreed 2026-09-28): `make test-positive` runs
# the ~48-call KB-correctness run among others.
# ---------------------------------------------------------------------------
test-type: fresh
	@test -n "$(TYPE)" || { echo "usage: make test-type TYPE=<$(TEST_TYPES)>"; exit 2; }
	@echo "$(TEST_TYPES)" | tr ' ' '\n' | grep -qx "$(TYPE)" || { echo "unknown TYPE=$(TYPE); one of: $(TEST_TYPES)"; exit 2; }
	@rc=0; \
	for suite in api judge sdk; do \
	  echo "=== $$suite: -m $(TYPE)"; \
	  (cd tests/$$suite && uv run pytest -v -rs -s -p no:cacheprovider -m "$(TYPE)" --junitxml=$(CURDIR)/report/data/junit/type-$(TYPE)-$$suite.xml); r=$$?; \
	  [ $$r -eq 5 ] && r=0; echo "=== $$suite exit=$$r"; [ $$r -ne 0 ] && rc=1; \
	done; \
	echo "=== ui: --grep @$(TYPE)"; \
	(cd tests/ui && npx playwright test --grep "@$(TYPE)\\b" --workers 1 --pass-with-no-tests); r=$$?; \
	echo "=== ui exit=$$r"; [ $$r -ne 0 ] && rc=1; \
	$(MAKE) --no-print-directory report-html; \
	exit $$rc

$(addprefix test-,$(TEST_TYPES)):
	@$(MAKE) --no-print-directory test-type TYPE=$(@:test-%=%)

check-types: fresh
	@for suite in api judge sdk; do \
	  (cd tests/$$suite && TEST_TYPES_STRICT=1 uv run pytest --collect-only -q -p no:cacheprovider > /dev/null) \
	    && echo "$$suite: every test has a testing type" || exit 1; \
	done
	@cd tests/ui && npx playwright test --list --reporter=json 2>/dev/null | python3 ../../tools/check_test_types.py

# NEWCOMER: one command from a fresh clone to a verified, ready-to-run project -
# toolchain (uv, Node, pnpm), .env, every dependency, Chromium, offline proof.
# Safe to re-run. See tools/setup.sh.
setup:
	@tools/setup.sh

install: install-ui install-api install-tools install-judge install-sdk

install-ui:
	cd tests/ui && (command -v pnpm >/dev/null && pnpm install || npm install)
	cd tests/ui && npx playwright install chromium

install-api:
	cd tests/api && uv sync

install-tools:
	cd tools && uv sync

# The judge's own dependencies are optional extras: `uv sync` alone installs
# enough to run the offline suite, which is the one that gates a PR. The judge
# model and the LiveKit SDK are only needed by the suites that cost money or
# open a session.
install-judge:
	cd tests/judge && uv sync --extra judge --extra live

# The LiveKit SDK suite. `stt` adds local speech-to-text (faster-whisper, CPU,
# ~150MB model on first use) for the audio/text consistency check; that one
# test skips without it.
install-sdk:
	cd tests/sdk && uv sync --extra stt

# Rebuild serial-index.json and scenarios.json from config/testbed.config.json.
# Run after renaming a KB file, adding a machine, or updating the workbook.
resources:
	cd tools && uv run python build_resources.py

catalog: fresh
	cd tests/api && uv run pytest tests/test_scenario_catalog.py -q $(JUNIT)

smoke: fresh
	cd tests/ui && npx playwright test --grep @smoke

regression: fresh
	cd tests/ui && npx playwright test --grep @regression

negative: fresh
	cd tests/ui && npx playwright test --grep @negative

# Everything that does not open a real agent session.
ui: fresh
	cd tests/ui && npx playwright test --grep-invert @live

# The real thing: opens sessions against the dev deployment.
chat: fresh
	cd tests/ui && npx playwright test --grep @chat

# DEMO: one live chat session, visible browser, one worker, readable output.
# The full positive path only - roughly 60-90 seconds.
demo: fresh
	cd tests/ui && npx playwright test -g "full positive workflow" --headed --workers 1

api: fresh
	cd tests/api && uv run pytest -v $(JUNIT)

# The rate-limiter contract. A dozen requests against a 100/minute window, so
# this is cheap enough to gate a PR on.
ratelimit: fresh
	cd tests/api && uv run pytest -v -m ratelimit $(JUNIT)

# Latency and payload budgets. Roughly 60 requests, and it self-throttles when
# the window runs low, so it can take longer than its test count suggests.
# Every run leaves its numbers in report/data/api-perf.json.
perf: fresh
	cd tests/api && uv run pytest -v -m perf $(JUNIT)

perf-report:
	@python3 -m json.tool report/data/api-perf.json 2>/dev/null || echo "no report/data/api-perf.json yet - run: make perf"

# SATURATION. This empties the shared rate-limit window, which blocks every
# other caller on this egress IP - CI, the browser suite, anyone clicking
# through the dev site - for up to a minute. Never in a PR check.
saturate: fresh
	cd tests/api && RUN_RATE_LIMIT_SATURATION=true uv run pytest -v -m load $(JUNIT)

# ---------------------------------------------------------------------------
# Semantic scoring. Reports, does not gate - judge.requireScoreGate is off, per
# docs/architecture.md: a borderline LLM score must never block a release on its
# own. Every run appends to report/data/judge-scores.json; the trend there is what
# the thresholds get re-based from.
# ---------------------------------------------------------------------------

# No network, no API account, no LiveKit. Validates the rubrics, that every one
# of the 221 scenarios resolves to the right KB section, and that the anchor
# matcher still agrees with the browser suite's. Cheap enough to gate a PR on,
# and it is the check that stops the expensive suites scoring confident nonsense.
judge-offline: fresh
	cd tests/judge && uv run pytest -v -m offline $(JUNIT)

# Scores the recordings in judge/recordings/ against their knowledge bases.
# One judge request per call. Needs ANTHROPIC_API_KEY in .env.
judge: fresh
	cd tests/judge && uv run pytest -v -m "offline or judged" $(JUNIT)

# Asks the deployment what its agent worker is called, rather than guessing.
# A wrong judge.livekit.agentName does not error - dispatch succeeds and nothing
# joins - so this is the first thing to run before any live suite. Needs network
# to the LiveKit host, so run it on the machine that owns .env.
probe-agent:
	cd tests/judge && uv run python -m src.livekit_probe

judge-report:
	@python3 -m json.tool report/data/judge-scores.json 2>/dev/null || echo "no report/data/judge-scores.json yet - run: make judge"

# ---------------------------------------------------------------------------
# The deterministic oracle. No model, no network, no credentials: a verdict
# that is a pure function of the transcript and the index compiled from the
# knowledge bases by `make resources`. Every gate in config.oracle.gates ships
# OFF, so this reports today and gates when a baseline says it should - see
# docs/deterministic-kb-testing.md.
# ---------------------------------------------------------------------------

# Runs inside `make judge-offline` too (it carries the `offline` marker); kept
# as its own target because it is the one to run after editing a KB.
oracle-offline: fresh
	cd tests/judge && uv run pytest -v -m offline tests/test_oracle.py $(JUNIT)

# Scores judge/recordings/. Override the directory with DIR=path/to/recordings.
oracle:
	cd tests/judge && uv run python -m src.oracle_cli $(if $(DIR),--dir $(abspath $(DIR)),)

oracle-report:
	@python3 -m json.tool report/data/oracle-verdicts.json 2>/dev/null || echo "no report/data/oracle-verdicts.json yet - run: make oracle"

# ---------------------------------------------------------------------------
# LiveKit SDK suite - sdk/. Joins real sessions exactly the way the product page
# does (the public assistant-session endpoint), with no browser, and scores
# every answer with judge/src/oracle.py. Every conversation is saved to
# report/data/recordings/ and every timing to report/data/livekit-sdk.json.
# -rs prints WHY anything skipped - a skip is never allowed to look like a pass.
# ---------------------------------------------------------------------------
SDK_PYTEST = cd tests/sdk && LKQA_REPORT_TAG=$@ uv run pytest -v -rs -p no:cacheprovider $(JUNIT)

livekit-offline: fresh
	$(SDK_PYTEST) -m offline

# Mints tokens, never joins: no agent is started. ~25 requests of the shared
# 100/minute window.
livekit-contract: fresh
	$(SDK_PYTEST) -m contract

livekit-auth: fresh
	$(SDK_PYTEST) -m auth

livekit-conversation: fresh
	$(SDK_PYTEST) -s tests/test_conversation.py

# The one that answers "is the answer actually coming from the knowledge base?".
# GROUNDING_RUNS=5 for the nightly k-run statistic.
livekit-grounding: fresh
	$(SDK_PYTEST) -s -m grounding

# Every anchored FAQ + one procedure per machine + general problems, each on a
# live call, each value judged against resources/kb/*.md. ~48 calls, 3 at a
# time, ~30 min. Results table: report/kb-correctness.md
livekit-kb: fresh
	$(SDK_PYTEST) -s -m kbrun

# Re-judge the KB run's recordings with today's checks - no calls made.
livekit-kb-rescore:
	cd tests/sdk && uv run python -m lkqa.kbrun

# Adaptive interview: a FREE LLM (Groq / Gemini, see .env.example) writes each next
# caller question from the KB as a follow-up to the agent's last answer, then judges
# the answer. One call per machine; INTERVIEW_TURNS / INTERVIEW_CALLS scale it.
livekit-interview: fresh
	$(SDK_PYTEST) -s -m interview

# Re-judge the last interview's saved answers with today's rules - no agent calls.
livekit-interview-rescore:
	cd tests/sdk && uv run python -m lkqa.interview

# Is the LLM key set, accepted, and is the configured model available?
llm-check:
	cd tests/sdk && uv run python -m lkqa.llm

# Positive corner cases: the same KB question in lowercase, ALL CAPS, with typos,
# filler, keywords only, as a statement, with hesitations, after a long preamble.
# One live call each (~8), judged like the KB run - the KB value or FAIL.
livekit-phrasing: fresh
	$(SDK_PYTEST) -s -m phrasing

livekit-voice: fresh
	$(SDK_PYTEST) -s -m voice

livekit-resilience: fresh
	$(SDK_PYTEST) -s tests/test_resilience.py

livekit-concurrency: fresh
	$(SDK_PYTEST) -s -m concurrency

livekit-browser: fresh
	cd tests/ui && npx playwright test tests/livekit --workers 1

livekit: livekit-offline livekit-contract livekit-auth livekit-conversation livekit-grounding \
         livekit-resilience livekit-voice livekit-concurrency livekit-browser

# REAL TRAFFIC ONLY: no mocks, no fixtures, no recorded calls. The API suite
# against the dev site, every SDK test that joins or talks to LiveKit (contract,
# auth, conversation, grounding, interview, voice, resilience, concurrency), then
# every browser test in a VISIBLE browser, one at a time. Excluded: sdk -m offline,
# the judge suite (scores saved recordings), and the @mock browser specs
# (page.route interception, fixed markup). LIVE_KB=1 adds the ~48-call KB run.
# Continues past a failing step so every suite reports.
LIVE_SDK_MARKERS = not offline$(if $(LIVE_KB),, and not kbrun)
live-headed: fresh
	@rc=0; \
	echo "=================== api (live)"; (cd tests/api && uv run pytest -v --junitxml=$(CURDIR)/report/data/junit/live-api.xml) || rc=1; \
	echo "=================== sdk (live: $(LIVE_SDK_MARKERS))"; \
	  (cd tests/sdk && uv run pytest -v -rs -s -p no:cacheprovider --junitxml=$(CURDIR)/report/data/junit/live-sdk.xml -m "$(LIVE_SDK_MARKERS)") || rc=1; \
	echo "=================== ui (headed, no @mock)"; \
	  (cd tests/ui && npx playwright test --headed --workers 1 --grep-invert @mock) || rc=1; \
	$(MAKE) --no-print-directory report-html; \
	exit $$rc

# The whole LiveKit SDK suite (sdk/), in PARALLEL: offline checks, then token and
# auth checks, then 3 live-call lanes (grounding | conversation+voice+resilience |
# interview), then the KB run, then concurrency. Never more than 3 live calls at
# once. No browser, no API suite. ~35 min instead of ~50 sequentially.
livekit-sdk: fresh
	@tools/run_parallel.sh sdk

# EVERYTHING in parallel, same waves as above plus the API, judge and browser
# suites (the browser suite is the third live lane). ~40 min instead of ~2 h.
all-parallel: fresh
	@tools/run_parallel.sh all

# REAL CALLS ONLY, 8 AT A TIME, VISIBLE BROWSER - no offline checks, no
# endpoint-only tests. Every answer judged against resources/kb. Every step its
# own lane (grounding, phrasing, interview, browser @live headed, conversation,
# voice, resilience: 7 calls at once), then the 48-call KB run 8 at a time, then
# concurrency (3 callers, by design). ~25 min. LIVE_PARALLEL=3 for the old pace.
live-parallel: fresh
	@tools/run_parallel.sh live

# The browser tests that hold a real agent call, in a visible browser, one at a time.
# On CI (no display; GitHub sets CI=true) the same tests run headless, unless
# FORCE_HEADED=1 - the "recorded browser" pipeline runs them headed on a virtual
# display (xvfb) with every call on video (PW_VIDEO=on).
ui-live-headed: fresh
	cd tests/ui && npx playwright test --grep @live --workers 1 $(if $(CI),$(if $(FORCE_HEADED),--headed,),--headed)

# Every browser test, live included, one worker (live tests must not overlap).
# HEADED=1 shows the browser.
ui-all: fresh
	cd tests/ui && npx playwright test --workers 1 $(if $(HEADED),--headed,)

livekit-report:
	@ls report/data/livekit-sdk*.json >/dev/null 2>&1 && for f in report/data/livekit-sdk*.json; do echo "== $$f"; python3 -m json.tool $$f; done || echo "no report/data/livekit-sdk*.json yet - run: make livekit-conversation"

# DEMO: one real call over the SDK - the dialogue as it happens, then the
# oracle's verdict on every figure the agent said, then the same recordings
# re-scored offline to show the verdict is deterministic. ~2 minutes.
demo-livekit: fresh
	$(SDK_PYTEST) -s tests/test_conversation.py
	$(MAKE) --no-print-directory oracle DIR=report/data/recordings

# Kept for muscle memory: the audio subset of the SDK suite.
voice: livekit-voice

test: api ui

# ---------------------------------------------------------------------------
# Reports
#   report/index.html          ONE page for every suite: totals, by testing type,
#                               every failure, KB-correctness table, LiveKit findings
#   report/playwright/  Playwright's own HTML report (traces, video, screenshots)
# ---------------------------------------------------------------------------
report:
	cd tests/ui && npx playwright show-report ../../report/playwright

report-html:
	@python3 tools/build_report.py

# SHAREABLE: one self-contained HTML file (styles, scripts, failure screenshots
# inside; tokens and keys redacted) - attach it to an email, Slack or Teams.
# Every run already writes report/qa-report.html; this also makes a dated copy
# in report/share/ so each one you send has its own name.
report-share: report-html
	@mkdir -p report/share; \
	f=report/share/qa-report-$$(date +%Y%m%d-%H%M).html; cp report/qa-report.html $$f; \
	echo "share this file: $$f ($$(du -h $$f | cut -f1))"

report-all: report-html
	@open report/index.html 2>/dev/null || xdg-open report/index.html 2>/dev/null || echo "open report/index.html in a browser"

# EVERYTHING, in order, cheapest first, then the combined report. Continues past a
# failing step so the report shows all of them. Live agent calls: ~100, ~2 hours.
all: fresh
	@rc=0; \
	for t in check catalog judge-offline livekit-offline check-types api livekit-contract livekit-auth \
	         livekit-conversation livekit-grounding livekit-kb livekit-interview livekit-phrasing livekit-voice livekit-resilience \
	         livekit-concurrency; do \
	  echo "=================== make $$t"; $(MAKE) --no-print-directory $$t || rc=1; \
	done; \
	echo "=================== ui (every browser test, live included)"; \
	(cd tests/ui && npx playwright test --workers 1) || rc=1; \
	$(MAKE) --no-print-directory oracle DIR=report/data/recordings || true; \
	$(MAKE) --no-print-directory report-html; \
	exit $$rc

clean:
	@$(MAKE) --no-print-directory fresh MAKELEVEL=0 FRESH=1
