# Thinknetic LiveKit agent: smoke test

This is the standard smoke test for the deployed Etnyre ChipSpreader support agent. It runs against one environment at a time: nonprod by default, or prod (see [Environments](#environments)). Every run executes two stages in order:

1. **Unit checks** (offline):
   - [kb/smoke.yaml](kb/smoke.yaml), the call's fixed inputs, is valid
   - the keyword check
   - reading the agent's logs
2. **LiveKit KB-steps call** ([test_kb_call.py](tests/sdk/tests/test_kb_call.py)). One live call to the deployed agent over the LiveKit SDK asks one fixed question, the same on every run. The answer passes when it contains every expected keyword. The caller then asks for the same steps to be texted to a different number (`SMS_TEST_PHONE`), and the text the agent sent is read from the agent's own logs and checked for the same keywords.

A failure in stage 1 stops the run before the live call. The HTML report is built every time, pass or fail.

The product-page UI test (Playwright) is no longer here. It now lives in its own repo.

## Run it

> [!IMPORTANT]
> **After every `git pull`, run the smoke test with a clean uv cache:**
>
> ```bash
> git pull
> uv cache clean && make smoke
> ```
>
> `uv cache clean` drops any stale cached packages so `make smoke` installs exactly what the pulled code expects.

First-time setup:

```bash
brew install livekit-cli    # the `lk` CLI, to read the agent's logs (CI installs it too)
cp .env.example .env        # fill in the nonprod section: LIVEKIT_URL, LIVEKIT_API_KEY,
                            # LIVEKIT_API_SECRET, SMS_TEST_PHONE
make smoke                  # clean, install, check-env, unit, kb, report - the same steps as CI
open report/index.html
```

| Command | What it does |
|---|---|
| `QA_ENV=prod make smoke` | The same run against prod. Works with every command below. |
| `make check-env` | Shows the environment's settings and where each one comes from (secrets are shown as "set"). Fails if one the live call needs is missing. |
| `make test` | The same sequence without the clean and install steps. |
| `make unit` | Unit checks only. Results go to the internal report, `report-internal/index.html`. |
| `make kb` | Live call only. |
| `make report` | Builds `report/index.html` from whatever has run. |
| `KB_SEED=123456789 make kb` | Repeats a run's exact model (and so serial). The seed is printed and shown in the report. |
| `KB_MODEL=FHRC28 make kb` | Pins the model, and so its serial. Any of the four models works here, but each has its own image store, and the image in [kb/smoke.yaml](kb/smoke.yaml) is confirmed only in FHRC28's and FHRC36's, so a VHRS model's image check can fail. |

The live test skips if the LiveKit credentials are missing, and fails with a clear message if another setting is missing or `SMS_TEST_PHONE` is the caller's own number.

## Environments

There are two: **nonprod** (the default) and **prod**. A setting has one name per environment, and the names are the same in a laptop's `.env` and in GitHub's secrets and variables. Nonprod's have no prefix; prod's start with `PROD_`:

```bash
LIVEKIT_URL=wss://…           # nonprod
PROD_LIVEKIT_URL=wss://…      # prod
```

Each environment has the LiveKit URL and keys, the agent name, `SMS_TEST_PHONE`, and the product IDs sent to the agent. [.env.example](.env.example) has the full layout, with nonprod's agent name and IDs filled in.

- **Pick the environment:** `QA_ENV=prod make smoke` locally. In CI, use the **environment** list under Actions → **qa** → **Run workflow**.
- **Where the settings come from:** on a laptop, `.env`. In CI, the repository secrets and variables of the same names (see [Settings in CI](#settings-in-ci)); CI never reads or writes a `.env`.
- **Change a value:** change its line in `.env`, and its secret or variable for CI. No code change and no commit.
- **Override for one run:** set the unprefixed name, for example `LIVEKIT_URL=wss://… make kb`.

A prod run only ever reads `PROD_` settings, so a blank `PROD_LIVEKIT_URL` stays missing. It never falls back to nonprod's value. `KB_SEED`, `KB_MODEL` and `TEST_CALLER_*` apply to both.

> [!WARNING]
> A live call is real in both environments. On prod it texts `PROD_SMS_TEST_PHONE`, creates a callback task, and writes a call log in prod's systems.

## The live call

Each run picks one of the two fixed-hopper models, FHRC28 or FHRC36, at random, and starts the call with that model's serial from [kb/smoke.yaml](kb/smoke.yaml). Whichever model it is, the caller asks the same question from that file, and the answer is checked for that file's keywords. The caller then asks to see the one image named in that file, the same on every call. Every call follows the same seventeen steps, and each one is a timed checkpoint in the report:

| # | Checkpoint | What happens |
|---|---|---|
| 1 | `call_started` | The test joins a fresh room and the agent is dispatched into it. The agent must join within 15 s. |
| 2 | `greeted` | The agent greets the caller. Serial look-up, read-back and the agent's "last time…" recap are all handled. |
| 3 | `question_asked` | The test caller asks the question from `kb/smoke.yaml`. |
| 4 | `answer_received` | The agent answers. It gives one step per turn, so the caller declines the offer to text the steps, declines the offer to put them on screen, asks for the complete procedure including cautions, and says "done, what's next?" after each step. Collecting stops when every keyword has been said, or at the turn limit. "Let me check" holding turns are ignored. |
| 5 | `answer_valid` | The combined answer must contain every keyword (rules below). |
| 6 | `image_triggered` | While the agent explains the steps, two things must happen, or the check fails (it is never skipped): its image tool searches its image store and pushes a picture to the caller's screen (`pushing_images` in its logs), and the test caller's screen receives it (the agent's `display_images` call). If the store has no picture for the topic, that is a failure, with the searches from the logs as the reason. |
| 7 | `image_requested` | The caller asks for the image in kb/smoke.yaml by its description, e.g. *Can you share a picture of the "Operator control panel or console"?*, and says yes if the agent asks to confirm. Two things must happen, or the check fails: **the image tool call** - within 40 s the `share_images` tool runs (`image_requested query=…`) and settles as shared (`image_request_settled status=shared`, or `discarded` when that picture was just shared), with the requested image as the one it shared (`image_outcome_noted … description=…`, matched on the description); and **the image received** - the test caller's screen gets that image (matched on its description). Another image, `not_found`, `failed`, no tool call, or no image on the screen fails, with the reason. |
| 8 | `text_asked` | The caller asks for the same steps by text. The agent offers the caller's own number; the caller refuses it, gives `SMS_TEST_PHONE` (a different number) and confirms the read-back. The agent must answer the request. |
| 9 | `text_triggered` | Checked from the agent's own logs (`lk agent logs`, followed for the whole call) **before the call moves on to thanks and the rating**. They must show the agent sent a text (`sending_text to=… message='…'`) to the `SMS_TEST_PHONE` number, not to the caller's. A refused delivery (for example a landline) never fails this. |
| 10 | `callback_asked` | The caller asks for a call back. The caller gives their own number (not the text number) as the callback number, and confirms it if asked. The agent must answer the request. |
| 11 | `callback_task_created` | Checked from the agent's own logs **before the call moves on to thanks and the rating**. They must show the `request_callback` tool call (`api_call_requested tool=request_callback args={'phone_number': …, 'reason': …}`) for the caller's own number, and an accepted (2xx) reply from the task service (`api_responded …/tasks status=201`). What the agent says is not enough; a refused or missing task fails this. |
| 12 | `thanks_sent` | The caller says thank you. This happens even if validation failed, so the report has the whole call. |
| 13 | `feedback_asked` | The agent must ask for a rating. |
| 14 | `feedback_answered` | The caller answers with a random integer from 1 to 10, which is logged. |
| 15 | `call_closed` | The agent must end the call within 30 s. The test always hangs up at the end, so no room is left open. |
| 16 | `text_valid` | After the call, the text the agent sent must contain every keyword too, like the spoken answer. |
| 17 | `call_log_complete` | After the call, checked from the agent's logs: the call record was written (transcript analysed, summary and notes extracted) and accepted (2xx) by the webhook. |

**Call length.** The call itself, from joining the room to hang-up, should take under **4:59**; the checks that run after it (text, call log) can take longer. `call_closed` shows how long each call took, and a call over 4:59 gets a note in the report. It is never cut short and never fails for this. Only a call that is genuinely stuck is stopped, after 8 minutes.

A failed call is retried once in a fresh room. The report shows that a retry happened and includes both transcripts.

**How the answer is checked.** The check is deterministic keyword matching, with no LLM judge ([validator.py](tests/sdk/lkqa/validator.py)).
- **What passes.** The answer passes when every keyword in `kb/smoke.yaml` (or one of its listed synonyms) is said somewhere in it. Order and the wording around the keywords don't matter, and nothing else is judged. A keyword matches whole words only, so "park" is not found in "parking".
- **Normalisation.** Both sides are normalised first: case, punctuation, curly quotes, spoken numbers ("forty to sixty" = "40–60"), units ("P S I" = PSI, "feet per minute" = FPM) and plurals.
- **What fails.** Any keyword that is never said. The report names each one.
- **The text.** The texted steps are checked for the same keywords, the same way.

## The question, keywords and serials

[kb/smoke.yaml](kb/smoke.yaml) holds everything the call needs. Edit it to change any of these; no code change is needed:

```yaml
serials:            # one per classification; the serial starts the call
  FHRC28: K7174
  FHRC36: K6758
  VHRS28: K7170
  VHRS36: K6757

question: I've finished my walk-around checks. Can you take me through starting the engine from the operator control panel, in the right order?

keywords:           # every one must be said, in any order
  - park
  - term: neutral
    synonyms: [centered, center position]
  - idle

image: Operator control panel or console   # the one picture every call asks to see
```

| Model | Serial | Machine |
|---|---|---|
| FHRC28 | K7174 | RC28, fixed hopper |
| FHRC36 | K6758 | RC36, fixed hopper |
| VHRS28 | K7170 | RC28, variable hopper |
| VHRS36 | K6757 | RC36, variable hopper |

The question and the picture go together. The start-up switches are on the operator control panel, so while the agent explains the steps its image tool should find and show the "Operator control panel or console" picture (`image_triggered`), and the caller then asks for the same picture by name (`image_requested`). The start-up order is in all four models' manuals, with the same first three steps: Park/Drive switch in PARK, joystick in neutral, Throttle Run/Idle switch in IDLE. So the same question and keywords work whichever serial is used. Each model resolves to its own product and image store. The picture is confirmed in FHRC28's and FHRC36's (both shared it on 2026-11-13); VHRS28's and VHRS36's are not confirmed yet. A keyword can list synonyms (`- term: neutral` with `synonyms: [center position]`); any one of them counts. Quote a keyword that YAML would read as true or false: `'on'`, `'off'`.

Every run checks the file first. It fails before the call, naming every problem, if:

- a model has no serial, or one that isn't FHRC28, FHRC36, VHRS28 or VHRS36 is given
- two models share a serial
- the question is empty
- there is no keyword, or a keyword is listed twice
- the image is missing or empty

## Read the report

`report/index.html` opens in any browser and works on a phone.

- **Banner.** PASS or FAIL for the whole run, with:
  - run time (IST), duration, branch and commit
  - the machine model and serial used
  - on failure, **Reference for what failed**: the LiveKit room ID (`RM_…`) and room name of every failed call. Search for these in LiveKit Cloud or the agent logs.
- **What was checked.** The phone-call check. The unit checks are not in this report.
- **The phone-call check.**
  - The question and its expected keywords.
  - For each attempt: **Call reference** (LiveKit room ID, room name, start time, agent participant), then **Question asked** (exactly as said on the call) and **Answer received** (the agent's answer turns, in order).
  - The seventeen checkpoints in plain English, each with its result and timing.
  - **The answer: expected keywords.** For every keyword: the sentence the agent said it in, or "Not said". The texted steps get the same table.
  - **The call, as it happened.** The full transcript as chat bubbles with timestamps, including the random rating.
- **Technical details.** A link to the raw call data and the exact command to re-run the same call.

## Branches

```
feature branch (e.g. develop-phase1_basic) --PR--> develop --PR--> master
```

- **Feature branches.** Work happens on a feature branch, and every feature branch merges into `develop` by pull request. The PR runs the smoke test, so a branch is tested before it merges.
- **`develop`** is the branch every test runs on. Each push to it, a merged PR included, runs the smoke test, and so does the daily schedule. It is the only branch whose report is published to GitHub Pages.
- **`master`** only receives `develop`, by pull request, when a release is ready.

To test a feature branch without opening a PR, run the workflow by hand and pick the branch under **Use workflow from**.

## CI

[.github/workflows/smoke.yml](.github/workflows/smoke.yml) (the **qa** workflow in the Actions tab) runs one suite per run:

| Trigger | Environment | Suite |
|---|---|---|
| Every pull request into `develop` | nonprod | `smoke`, always |
| Every push to `develop` (a merged PR included) | nonprod | `smoke`, always |
| Monday to Friday at 06:00 IST (scheduled), on `develop` | nonprod | `smoke`, always |
| Manual: Actions → **qa** → **Run workflow**, on the branch you pick | the one you pick from the **environment** list (NONPROD, PROD) | the one you pick from the **suite** list |

| Suite | What it runs |
|---|---|
| `smoke` | Unit checks, then the live call. A unit failure stops it before the call. |
| `unit` | Unit checks only (offline). |
| `live` | The live call only. |

A manual run can also set the seed or the model. GitHub only runs scheduled workflows from the default branch, so the daily run needs `develop` to be the default branch. Before the live call, `make check-env` fails the run if a setting the call needs is missing. Runs on the same environment wait for each other; different environments can run at the same time.

- It starts from a clean slate: no restored caches and old reports removed.
- Every stage in the chosen suite must pass. Stages outside it show as "not in suite".
- Every run that makes a live call (`smoke`, `live`) builds the report, pass or fail:
  - **GitHub Pages** holds the latest call run on `develop`, from whichever environment ran last; the report names it. The link is in the run summary. Runs on a PR or another branch, and `unit` runs, never replace it.
  - **The `<environment>-<suite>-report-<n>` artifact** keeps every run.
- The unit checks are not in that report. They go to `report-internal/index.html`, kept as the separate `<environment>-internal-unit-checks-<n>` artifact and never published to Pages.
- One-time setup:
  - The settings, as repository secrets and variables: see [Settings in CI](#settings-in-ci).
  - Settings → Pages → Source = **GitHub Actions**.
  - Settings → General → Default branch = `develop`, for the daily run.
  - Settings → Environments → `github-pages` → Deployment branches: add `develop`, so its runs can publish.

### Settings in CI

CI reads each setting from the repository secret, or else the repository variable, with the same name as in `.env` (Settings → Secrets and variables → Actions). It writes no `.env` and never prints a secret. If one is missing, `make check-env` fails the run before the call and names it.

| Setting | Nonprod | Prod | Keep it as |
|---|---|---|---|
| LiveKit project | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | `PROD_LIVEKIT_URL`, `PROD_LIVEKIT_API_KEY`, `PROD_LIVEKIT_API_SECRET` | secrets |
| Number that receives the test text | `SMS_TEST_PHONE` | `PROD_SMS_TEST_PHONE` | secret |
| Agent and product | built in ([env.py](tests/sdk/lkqa/env.py) `NONPROD_DEFAULTS`); a variable `AGENT_NAME`, `PRODUCT_NAME`, `PRODUCT_BRAND`, `ORGANIZATION_ID`, `ORG_SLUG`, `KNOWLEDGE_BASE_ID`, `ASSISTANT` or `AGENT_ID` overrides one | `PROD_AGENT_NAME`, `PROD_PRODUCT_NAME`, … all required; optionally `PROD_AGENT_ID` | variables |

So nonprod needs only its four secrets, which the repository already has. Keep the agent and product settings as variables, not secrets: they are not secret, and GitHub hides every occurrence of a secret's value in the logs (as a secret, `ORG_SLUG` = `e` would hide every letter "e").

## Layout

```
kb/smoke.yaml                       the four serials, the question, its keywords and the image
tests/sdk/lkqa/env.py               QA_ENV, and each setting's name and source (.env, or CI's secrets)
tests/sdk/lkqa/smoke.py             loads kb/smoke.yaml; picks the model and so the serial (seeded)
tests/sdk/lkqa/kbcall.py            the seventeen-checkpoint live call
tests/sdk/lkqa/validator.py         deterministic keyword check
tests/sdk/lkqa/expect.py            LiveKit-style expect() assertions over the recorded call
tests/sdk/lkqa/call.py              LiveKit room, agent dispatch token, turn reading
tests/sdk/lkqa/agentlogs.py         the agent's own logs (lk agent logs): text, callback task, images, call log
tests/sdk/tests/                    test_kb_call.py (live), test_smoke / test_validator /
                                    test_images / test_agentlogs / test_env (offline)
tools/build_report.py               report/index.html
tools/check_env.py                  make check-env
```
