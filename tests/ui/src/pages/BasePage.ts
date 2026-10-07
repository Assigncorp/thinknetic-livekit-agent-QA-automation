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
}
