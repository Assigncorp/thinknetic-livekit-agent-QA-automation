import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
// .env lives at the repo root, shared with the SDK suite.
dotenv.config({ path: path.resolve(here, '..', '..', '.env') });

export default defineConfig({
  testDir: './tests',
  outputDir: '../../report/data/ui-artifacts',
  // A shared dev deployment: one test at a time, so a run is never a load test.
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: Number(process.env.UI_TIMEOUT_MS ?? 60_000),
  expect: { timeout: 10_000 },
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../report/playwright', open: 'never' }],
    // Read by tools/build_report.py for report/index.html.
    ['json', { outputFile: '../../report/data/ui-results.json' }],
  ],
  use: {
    baseURL: process.env.BASE_URL ?? 'https://etnyre-dev.thinknetic.app',
    headless: process.env.HEADLESS !== 'false',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // The microphone is deliberately NOT pre-granted (nor auto-accepted with
    // --use-fake-ui-for-media-stream): the page's welcome dialog only shows
    // while it is not, and the UI test checks that dialog, then grants it.
    launchOptions: {
      args: [
        '--use-fake-device-for-media-stream',
        '--autoplay-policy=no-user-gesture-required',
      ],
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
