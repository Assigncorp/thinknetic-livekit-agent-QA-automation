# Daily cloud test of the Enterprises `settings.yaml`

**Owner:** QA automation (`thinknetic-livekit-agent-QA-automation`)
**Subject under test:** `src/assistants/product_support/config/enterprises-product-support-assistant/settings.yaml` in `Assigncorp/thinknetic-livekit-agents`
**Runs:** every day at **06:00 IST** (00:30 UTC) on GitHub Actions, plus on demand
**Status:** plan. The test files and workflow below are proposed and do not exist yet.

---

## 1. Goal and the one rule

Each morning, check that the settings the agent is actually running behave as the file says.

**The rule: the settings file is never copied into the QA repo.** Every run pulls it fresh from the agent repo, so QA always tests what the agent team last committed. A stale copy would pass while production drifts.

```
06:00 IST  ->  GitHub Actions (QA repo)
                 |- checkout QA repo                       (tests, question bank)
                 |- checkout thinknetic-livekit-agents     (settings.yaml + phrases.yaml, read-only, fresh)
                 |- Layer 1  static config tests           (no network, seconds)
                 |- Layer 2  live call + agent-log checks  (LiveKit Cloud, nonprod agent)
                 |- Layer 3  drift check, S3 vs repo       (optional, needs AWS read)
                 '- HTML report + Pages + failure alert
```

Background that shapes the design: `settings.yaml` is the baked-in fallback. The business-editable copy is the S3 object `{prefix}/enterprises-product-support-assistant/settings.yaml`. Layer 3 exists because of that.

---

## 2. What each layer tests

### Layer 1: static tests (offline, `pytest -m offline`)

Fast and free. They fail the run before any live call is placed.

| ID | Block | Check |
|---|---|---|
| S-01 | whole file | Parses as YAML; top-level `system_settings:` exists; no unknown top-level keys |
| S-02 | `kb` | `database_url_env_key` is set and the named variable is declared in the agent's env list; booleans are booleans |
| S-03 | `kb` | `0 < max_distance <= 2`, `0 < image_max_distance <= 2`; `image_max_distance <= max_distance`; `filler_after_seconds >= 0`; `image_timeout_seconds > 0` |
| S-04 | `resume_last_session_within_days` | Integer `>= 0` |
| S-05 | `serial_number_formats` | Each pattern uses only `A`/`#`/punctuation; **all serials in `kb/smoke_serials.yaml` match one**; repair of "K7O23" gives K7023 (calls the same repair logic if importable, otherwise a reimplementation guarded by a comment) |
| S-06 | `pronunciations` | Keys and values are non-empty strings; no spelling listed under two respellings; every product or brand name in the KB question bank is either covered or knowingly absent |
| S-07 | `integrations.http_endpoints` | URL is `https`; `method` valid; `timeout_seconds` > 0; `credentials.type` in `bearer / api_key / oauth2`; `env_key` is a **name**, not a token |
| S-08 | `http_endpoints` vs `phrases.yaml` | Every tool key has `tool_schema.<name>`, `say.arranging_callback` and `instructions.error.<name>_failed` in `phrases.yaml`. This is the "better no tool than a broken one" rule |
| S-09 | `request_callback.body_template` | Renders with sample values and with empty values (`default("NA", true)` path); output is valid JSON; no unresolved `{{ }}` left; `omit_empty` prunes the product attribute when `product_id` is blank |
| S-10 | `sms` | `from_number` is E.164; `default_country_code` is digits |
| S-11 | `transfer` | `timezone` is a valid IANA name (not `CST` or `+05:30`); `timeout_seconds` > 0; `sip_trunk_id` non-empty |
| S-12 | `transfer.destinations` | Every `keywords` value is in the `transfer_to_human.keyword` enum from `phrases.yaml`; `to_number` and `from_number` are E.164; `dtmf` uses only `0-9 * # A-D w` |
| S-13 | `transfer.available` | **Coverage grid.** Evaluate all 10,080 minutes of a week in `timezone`. For each keyword (`part`, `other`) exactly one destination is open every minute, or the gap is explicitly allowed. Also pins edge minutes: Mon 06:59, 07:00, 16:59, 17:00, 17:01, Sat 00:00, Sun 23:59 |
| S-14 | `transfer` safety | Every `to_number` is in an approved test-number allow-list (`TRANSFER_TEST_NUMBERS`). Fails loudly the day someone commits a real desk number to nonprod config |
| S-15 | `transcriber` | `provider`/`model` pair is in a known-good list (deepgram / nova-3); boolean flags are booleans |
| S-16 | `model` | `provider`/`model` in the allow-list; `0 <= temperature <= 2`; `max_tool_steps` between 1 and 50. **Guard:** an Anthropic model that rejects `temperature` (the file's own comment warns about this) fails here |
| S-17 | `voice` | List is non-empty; each item names a `provider`; Cartesia `speed` within 0.6-1.5; ElevenLabs `voice_id` present; **at least two providers** so there is always a fallback; the required key (`CARTESIA_API_KEY`, `ELEVENLABS_API_KEY`) is declared for each |
| S-18 | `noise_cancellation` | `enabled` is boolean |
| S-19 | `turn_handling` | `turn_model` in `en / multilingual / off`; `endpointing.min_delay <= max_delay`; `mode` in `fixed / dynamic`; `interruption.min_words >= 0`, `min_duration >= 0`. **Guard:** `multilingual` requires the model files in the image (checked against the Dockerfile download step) |
| S-20 | `message_plan` | `idle_timeout_seconds > 0`; `idle_messages` non-empty; `idle_message_max_spoken_count >= 1`; `idle_end_message` renders its placeholders |
| S-21 | `max_duration_seconds` | `>= 0`; the cap is greater than idle timeout times nudge count; message renders |
| S-22 | `end_call.structured_data` | `schema` is valid JSON Schema; every `required` key exists in `properties`; `additionalProperties: false`; prompt placeholders all belong to the known set (`organization_name`, `product_name`, `product_serial_number`, ...) |
| S-23 | `end_call.webhook` | URL is `https`, not `localhost`, and host is on the allow-list |
| S-24 | placeholders | Every `{{ placeholder }}` anywhere in the file resolves against the dispatch metadata the test sends (`product_brand`, `organization_id`, ...) |
| S-25 | snapshot | Hash of the whole file is recorded in the report; the diff against yesterday's hash is shown so a failure can be traced to a commit |

### Layer 2: live call against the nonprod agent

Reuses the existing 14-checkpoint call (KB steps, SMS, callback) and adds settings-driven checkpoints. The agent is `thinknetic-agents-nonprod` on LiveKit Cloud, and checks that need proof come from `lk agent logs`, as `text_triggered` and `callback_task_created` do today.

| ID | Block | How it is checked |
|---|---|---|
| L-01 | `kb` retrieval, hybrid, `max_distance` | **Already covered.** The answer must match the KB steps and cautions (existing validator) |
| L-02 | `kb.filler_after_seconds` | Log shows the filler line only when a lookup exceeds 5 s; otherwise silence. Soft check: reported, fails only on a clear contradiction |
| L-03 | `kb.capture_search_metrics` | Log or DB shows one measured search row for the call (confirm exact log event name with the agent team) |
| L-04 | `kb.image_search_enabled` | Log shows the image side-channel started and finished inside `image_timeout_seconds` |
| L-05 | `serial_number_formats` | Caller says "K seven O two three"; the agent's log or state shows the serial repaired to K7023 and the model routes correctly |
| L-06 | `resume_last_session_within_days` | Second call within the window with the same serial: agent offers to resume. Call 1 is the main smoke call; call 2 is short |
| L-07 | `integrations...request_callback` | **Already covered** (`callback_task_created`: tool call plus a 2xx reply). Add: body in the log contains the title "Callback requested", the serial, and the phone number |
| L-08 | `sms` | **Already covered** (`text_triggered`, sent to `SMS_TEST_PHONE`). Add: `from_number` in the log equals the configured one |
| L-09 | `message_plan` idle | Separate short call: caller stays silent. Expect nudge 1 at about 15 s ("Are you still there?"), nudge 2 at about 30 s, end message after the third. Tolerance of plus or minus 3 s |
| L-10 | `message_plan.smart_llm_wait_detection` | Caller says "give me a second": no nudge is spoken for that wait |
| L-11 | `end_call.webhook` | Log shows `call_log_delivered` (already used by `agentlogs.py` as the end marker) and a 2xx webhook reply |
| L-12 | `end_call.structured_data` | Delivered record contains `call_summary` and at least one `notes` item, and nothing outside the schema |
| L-13 | `transcriber` | Spoken serial and phone digits come out as digits in the transcript (`numerals: true`, `smart_format: true`) |
| L-14 | `turn_handling.interruption` | Caller barges in during the agent's answer: the agent stops within about 1 s. Latency figures are recorded and trended, not hard-failed |
| L-15 | `turn_handling.endpointing` | Time from end of caller speech to start of agent reply is recorded and trended. Hard-fail only above a generous ceiling (for example 5 s) |
| L-16 | `voice` | Agent audio is produced for the whole call (no TTS failure line in the log). Log must show which provider spoke so a silent fallback is visible |
| L-17 | `model` | Log shows the configured provider/model for the session (catches an accidental swap) |
| L-18 | `noise_cancellation` | Log shows the noise-cancellation model attached to the session (telephony vs standard) |
| L-19 | `transfer` routing (opt-in, `TRANSFER_LIVE=1`) | Caller asks for a human. From the log assert the **chosen destination and DTMF string** match what the schedule says for the current minute in `America/Chicago`. The test hangs up as soon as the dial is logged. Off by default because all destinations ring a real test phone |
| L-20 | `pronunciations` | The text sent to TTS (if logged) contains `Et-nire` where the agent said "Etnyre", while the transcript keeps the real spelling. If TTS input is not logged, this stays static (S-06) |

### Layer 3: drift check (optional, needs read access to S3)

| ID | Check |
|---|---|
| D-01 | S3 object `{prefix}/enterprises-product-support-assistant/settings.yaml` parses and passes **all of Layer 1** exactly like the repo copy |
| D-02 | Keys that exist in S3 but not in the repo fallback (and the reverse) are listed |
| D-03 | Differences in values are listed in the report. Differences that touch `transfer`, `integrations`, `end_call.webhook` or `model` fail the run |
| D-04 | The S3 copy contains no secret-looking strings (long tokens, `sk-`, `Bearer `) |

### Not worth testing daily

| Setting | Why | Where it is covered |
|---|---|---|
| `max_duration_seconds: 1800` | A 30-minute call every morning wastes minutes and money | S-21 daily. Weekly job with a 60 s override in a nonprod variant |
| Voice quality and naturalness of Cartesia vs ElevenLabs | A human listening task | Cekura or manual review |
| Real phone ring of every transfer desk | Rings real phones | L-19 stops at the dial |

---

## 3. Files to add to the QA repo

```
.github/workflows/settings-daily.yml
tests/sdk/lkqa/settings_model.py          loads settings.yaml + phrases.yaml from $AGENT_SRC
tests/sdk/lkqa/cronwindow.py              minute-grid evaluator for transfer.available
tests/sdk/tests/test_settings_static.py   S-01 .. S-25   (marker: offline)
tests/sdk/tests/test_settings_drift.py    D-01 .. D-04   (marker: drift)
tests/sdk/tests/test_settings_live.py     L-01 .. L-20   (marker: live)
tests/sdk/lkqa/kbcall.py                  extended with the extra checkpoints
kb/settings_expectations.yaml             allow-lists (providers, test numbers, hosts, placeholders)
```

`pyproject.toml`: add `croniter`, `jsonschema`, `jinja2`, `boto3` (drift only), and a `drift` marker.

Environment for the tests:

| Variable | Meaning |
|---|---|
| `AGENT_SRC` | Path of the checked-out agent repo (`agents-src` in CI) |
| `SETTINGS_REL` | `src/assistants/product_support/config/enterprises-product-support-assistant` |
| `AGENTS_SHA` | Commit that was checked out; printed in the report |
| `TRANSFER_TEST_NUMBERS` | Comma-separated allow-list used by S-14 |
| `TRANSFER_LIVE` | `1` to enable L-19 |
| `S3_SETTINGS_URI` | Used by D-xx; unset means the drift stage is skipped, and the report says so |

### Skeleton: loader and two key tests

```python
# tests/sdk/lkqa/settings_model.py
import os, pathlib, yaml

def _dir() -> pathlib.Path:
    return pathlib.Path(os.environ["AGENT_SRC"]) / os.environ["SETTINGS_REL"]

def load():
    d = _dir()
    s = yaml.safe_load((d / "settings.yaml").read_text())["system_settings"]
    p = yaml.safe_load((d / "phrases.yaml").read_text())
    return s, p
```

```python
# tests/sdk/tests/test_settings_static.py
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from croniter import croniter
from lkqa.settings_model import load

pytestmark = pytest.mark.offline
S, P = load()

def test_s08_every_endpoint_has_phrases():
    for tool in S["integrations"]["http_endpoints"]:
        assert tool in P["tool_schema"], f"{tool}: no tool_schema in phrases.yaml"

def test_s13_transfer_has_no_coverage_gap():
    tr = S["transfer"]
    tz = ZoneInfo(tr["timezone"])
    start = datetime(2026, 1, 5, 0, 0, tzinfo=tz)          # a Monday
    gaps = []
    for kw in ("part", "other"):
        dests = [d for d in tr["destinations"] if kw in d["keywords"]]
        for m in range(7 * 24 * 60):
            t = start + timedelta(minutes=m)
            open_now = [d for d in dests
                        if any(croniter.match(c, t.replace(tzinfo=None)) for c in d.get("available", ["* * * * *"]))]
            if len(open_now) != 1:
                gaps.append((kw, t.isoformat(), len(open_now)))
    assert not gaps, f"{len(gaps)} minutes with 0 or 2+ open desks, first: {gaps[:3]}"
```

(Two desks open at once is only a failure if the order does not decide it. Adjust the assertion to the "first open destination wins" rule the file documents.)

---

## 4. The daily workflow

Create a **new** file, `.github/workflows/settings-daily.yml`, so the existing `smoke.yml` is untouched. Both use `concurrency: group: smoke`, so they never place live calls at the same time.

```yaml
name: settings-daily

on:
  schedule:
    - cron: "30 0 * * *"        # 06:00 IST = 00:30 UTC, every day
  workflow_dispatch:
    inputs:
      agents_ref:
        description: "Agent repo branch/tag/SHA to test (blank = develop)"
        required: false
      transfer_live:
        description: "1 = also run the transfer routing check"
        required: false

concurrency:
  group: smoke
  cancel-in-progress: false

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  settings:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    env:
      LIVEKIT_URL: ${{ secrets.LIVEKIT_URL }}
      LIVEKIT_API_KEY: ${{ secrets.LIVEKIT_API_KEY }}
      LIVEKIT_API_SECRET: ${{ secrets.LIVEKIT_API_SECRET }}
      SMS_TEST_PHONE: ${{ secrets.SMS_TEST_PHONE }}
      AGENT_NAME: thinknetic-agents-nonprod
      AGENT_SRC: ${{ github.workspace }}/agents-src
      SETTINGS_REL: src/assistants/product_support/config/enterprises-product-support-assistant
      TRANSFER_TEST_NUMBERS: ${{ vars.TRANSFER_TEST_NUMBERS }}
      TRANSFER_LIVE: ${{ inputs.transfer_live }}
      S3_SETTINGS_URI: ${{ vars.S3_SETTINGS_URI }}
      KB_RETRIES: "1"
      CI: "true"
    steps:
      - uses: actions/checkout@v4                       # QA repo

      # Always the latest agent config - never a copy kept in this repo.
      - name: Fetch the agent repo (config only)
        uses: actions/checkout@v4
        with:
          repository: Assigncorp/thinknetic-livekit-agents
          ref: ${{ inputs.agents_ref || 'develop' }}
          token: ${{ secrets.AGENTS_REPO_READ_TOKEN }}
          path: agents-src
          sparse-checkout: |
            src/assistants/product_support/config
            Dockerfile
          fetch-depth: 1

      - name: Record what is being tested
        run: |
          sha=$(git -C agents-src rev-parse HEAD)
          echo "AGENTS_SHA=$sha" >> "$GITHUB_ENV"
          sha256sum "agents-src/$SETTINGS_REL/settings.yaml" | tee settings.sha256
          echo "SMOKE_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"

      - name: Check the secrets are set
        run: |
          for v in LIVEKIT_URL LIVEKIT_API_KEY LIVEKIT_API_SECRET SMS_TEST_PHONE; do
            [ -n "${!v}" ] || { echo "::error::secret $v is not set"; missing=1; }
          done
          test -z "${missing:-}"

      - uses: astral-sh/setup-uv@v6
        with: { enable-cache: false }
      - run: make install
      - name: Install the LiveKit CLI
        run: curl -sSL https://get.livekit.io/cli | bash

      - name: Layer 1 - static settings tests
        id: static
        continue-on-error: true
        run: cd tests/sdk && uv run pytest tests/test_settings_static.py -m offline --junitxml=../../report-internal/junit-settings-static.xml

      - name: Layer 3 - drift check (S3 vs repo)
        id: drift
        if: env.S3_SETTINGS_URI != ''
        continue-on-error: true
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_READ_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - name: Layer 3 - run
        if: env.S3_SETTINGS_URI != '' && steps.drift.outcome == 'success'
        continue-on-error: true
        run: cd tests/sdk && uv run pytest tests/test_settings_drift.py -m drift

      - name: Layer 2 - live call + agent-log checks
        id: live
        if: steps.static.outcome == 'success'          # a broken config is not worth a phone call
        continue-on-error: true
        run: cd tests/sdk && uv run pytest tests/test_settings_live.py tests/test_kb_call.py -m live --junitxml=../../report/data/junit-settings-live.xml

      - name: Build the report
        if: always()
        run: make report

      - name: Keep the reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: settings-daily-${{ github.run_number }}
          path: |
            report/
            report-internal/
            settings.sha256

      - name: Verdict
        if: always()
        run: |
          {
            echo "## Settings daily test"
            echo "Agent repo commit: \`$AGENTS_SHA\`"
            echo "| Layer | Result |"
            echo "|---|---|"
            echo "| 1 static | ${{ steps.static.outcome }} |"
            echo "| 3 drift  | ${{ steps.drift.outcome }} |"
            echo "| 2 live   | ${{ steps.live.outcome }} |"
          } >> "$GITHUB_STEP_SUMMARY"
          test "${{ steps.static.outcome }}" = success
          test "${{ steps.live.outcome }}" = success

      - name: Alert on failure
        if: failure()
        run: |
          curl -sS -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"settings-daily FAILED - agent commit $AGENTS_SHA - $GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID\"}" \
            "${{ secrets.ALERT_WEBHOOK_URL }}"
```

Simplifications to make when implementing: split Layer 3 into its own job if the AWS step gets awkward, and add the report publish job from `smoke.yml` unchanged.

---

## 5. One-time setup

1. **Cross-repo read access.** Create a fine-grained token with *Contents: read* on `Assigncorp/thinknetic-livekit-agents` only. Save it in the QA repo as the secret `AGENTS_REPO_READ_TOKEN`. (A deploy key also works.)
2. **Secrets already used by `smoke.yml`:** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `SMS_TEST_PHONE`.
3. **New repo variables:** `TRANSFER_TEST_NUMBERS` (for example `+18182477100`), and for Layer 3 `S3_SETTINGS_URI`, `AWS_REGION`. New secrets: `AWS_READ_ROLE_ARN` (read-only role on that one S3 key, via GitHub OIDC), `ALERT_WEBHOOK_URL`.
4. **GitHub scheduled workflows only run from the default branch.** `smoke.yml` currently targets `develop-phase1_basic`; this workflow must be merged to the default branch (`master`) before 06:00 runs begin. Until then use **Run workflow** to test it manually.
5. **Time zone.** The cron is UTC. `30 0 * * *` is 06:00 IST. GitHub can start a scheduled run several minutes late at busy times, so expect a start between 06:00 and about 06:20 IST.
6. **Agent log names.** L-02, L-03, L-04, L-05, L-17 and L-18 need log events that are not documented in this repo's README. Ask the agent team for the exact event names (the existing ones are `sending_text`, `api_call_requested`, `api_responded`, `call_log_delivered`, `voice_session_closed`). Until then, those checks should be marked `xfail` with the reason "log event not available" so they show in the report without failing the run.

---

## 6. Pass and fail policy

| Result | Meaning | Action |
|---|---|---|
| Layer 1 fails | The config is wrong or breaks a rule. No live call is placed | Alert, link to the agent commit |
| Layer 3 fails on a **critical** key (`transfer`, `integrations`, `webhook`, `model`) | S3 and the repo disagree on something that matters | Alert |
| Layer 2 hard check fails | The deployed agent does not behave as configured | Retry once in a fresh room (existing behaviour), then alert |
| Layer 2 soft check (L-02, L-14, L-15) | Latency or timing outside the usual band | Shown in the report and trended; never fails alone |
| Skipped stage | A required secret or log event is missing | Report says **skipped** in a distinct colour. A skip is never shown as a pass |

## 7. Report additions

Add to the existing `report/index.html`:

- the agent repo commit tested and the SHA-256 of `settings.yaml`, with a "changed since yesterday" flag
- one row per ID in section 2 with Pass / Fail / Skipped / Soft-warn and a one-line reason
- the transfer coverage grid as a small weekly heat strip (S-13)
- yesterday-vs-today for latency figures (L-14, L-15)
- the LiveKit room IDs of every call placed

## 8. Rollout order

1. **Day 1:** Layer 1 (S-01 to S-25) plus the workflow and the 06:00 schedule. This alone catches most bad edits and costs nothing.
2. **Week 1:** L-05, L-07, L-08, L-11, L-12, L-17 (they reuse the log reader that already exists).
3. **Week 2:** L-06 and L-09/L-10 (extra short calls), then Layer 3.
4. **Later:** L-19 with a safe test destination, a weekly 60-second `max_duration` variant, and Cekura persona scenarios for turn-taking quality.

## 9. Risks and open items

- **Cost and noise.** Each morning places 1 main call plus up to 2 short ones, and sends one real SMS to `SMS_TEST_PHONE`. Keep the extra calls short.
- **A shared nonprod agent.** The live call uses `thinknetic-agents-nonprod`. If it is redeployed during the 06:00 window, the run can fail for reasons unrelated to settings. The retry covers most of this.
- **Which branch is deployed.** The plan tests `develop` by default. Confirm that the nonprod agent is built from `develop`; if not, set `agents_ref` to the branch it is built from, otherwise Layer 1 and Layer 2 test different things.
- **Secrets in the file.** The config holds phone numbers, an SIP trunk id and a webhook host. Do not print the file in logs or publish it to Pages; the report should show hashes and parsed values only for the keys it asserts on.
- **Unverified assumptions.** The log event names above, the `transfer_to_human.keyword` enum layout in `phrases.yaml`, and the exact import path of the serial-repair code were not checked against the agent repo. Verify them when writing S-05, S-08, S-12 and L-05.
