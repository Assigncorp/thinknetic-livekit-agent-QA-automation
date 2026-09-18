# Troubleshooting

### `make install` fails on `uv: command not found`
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then restart the shell.

### Playwright cannot find a browser
`cd ui && npx playwright install chromium`. Browsers live outside the repo, so a
fresh clone always needs this.

### Every UI test fails at `expect(talkToMe).toBeVisible()`
Either the dev deployment is down (run `make api` — it takes seconds and will
tell you), or the button's label changed. Fix it in `ui/src/selectors.ts`, not
in the test.

### The `@live` session tests fail but everything else passes
Most likely a session panel selector. Run
`cd ui && npx playwright test --grep @live --headed`, watch what actually renders, and
correct `sel.chatWidget` (the panel's controls, shared by voice and text) or
`sel.callerIntake` (the "Before we start" form) in `ui/src/selectors.ts`.

### Chrome asks for microphone permission during a run
The permission should be pre-granted by `playwright.config.ts`. If a prompt
appears, the launch args did not apply — check you are running the `chromium`
project and not a system browser via `--browser`.

### Tests pass locally and fail in CI
CI runs headless Linux Chromium with 2 workers. Usual causes: a timing
assumption that holds on a fast laptop, or a test that is not order-independent.
Reproduce with `CI=true npx playwright test`.

### A test is flaky
Do not add a retry and move on. Open the trace — `make report`, click the failed
test, scrub the timeline. Playwright traces show the DOM at each step, which
almost always makes the race obvious.

### `__pycache__` folders appear in the repo
Normal Python behaviour; they are gitignored. Ignore them.
