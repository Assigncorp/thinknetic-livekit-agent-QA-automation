import type { Page } from '@playwright/test';
import { TIMEOUT } from '../constants/timeouts.js';

/**
 * Shared behaviour for every page object. Keep this thin - a fat base class is
 * how page objects turn into a second application nobody maintains.
 */
export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  async goto(path: string): Promise<void> {
    await this.page.goto(path, {
      waitUntil: 'domcontentloaded',
      timeout: TIMEOUT.navigation,
    });
  }

  /** Screenshot into the reports folder, for ad-hoc debugging. */
  async capture(name: string): Promise<void> {
    await this.page.screenshot({
      path: `../reports/screenshots/${name}-${Date.now()}.png`,
      fullPage: true,
    });
  }

  async dismissOverlays(): Promise<void> {
    // Cookie/consent banners have not appeared on dev. If one shows up, decline
    // non-essential cookies here rather than in individual tests.
  }
}
