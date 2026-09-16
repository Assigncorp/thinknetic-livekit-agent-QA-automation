import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
// .env lives at the repo root so both toolchains read the same values.
dotenv.config({ path: path.resolve(here, '..', '.env') });

const BASE_URL = process.env.BASE_URL ?? 'https://etnyre-dev.thinknetic.app';
const HEADLESS = process.env.HEADLESS !== 'false';

export default defineConfig({
  testDir: './tests',
  outputDir: '../reports/ui-artifacts',
  // The app under test is a shared dev deployment - keep concurrency modest
  // so we do not create a self-inflicted load test.
  workers: process.env.CI ? 2 : 3,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: Number(process.env.UI_TIMEOUT_MS ?? 30_000),
  expect: { timeout: 10_000 },

  reporter: [
    ['list'],
    ['html', { outputFolder: '../reports/playwright-report', open: 'never' }],
    ['json', { outputFile: '../reports/ui-results.json' }],
  ],

  use: {
    baseURL: BASE_URL,
    headless: HEADLESS,
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // The agent widget asks for the microphone. Granting it here means no
    // human has to click the Chrome permission bubble mid-run.
    permissions: ['microphone'],
    launchOptions: {
      slowMo: Number(process.env.SLOW_MO ?? 0),
      args: [
        '--use-fake-ui-for-media-stream',
        '--use-fake-device-for-media-stream',
        '--autoplay-policy=no-user-gesture-required',
      ],
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Enable once the desktop suite is stable; the widget layout differs on mobile.
    // { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
  ],
});
