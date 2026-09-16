import { expect, type Page, type Response } from '@playwright/test';
import { sel } from '../selectors.js';
import { api, routes } from '../config/env.js';

/**
 * The public product support page - entry point for both voice and chat modes.
 */
export class ProductPage {
  constructor(private readonly page: Page) {}

  /**
   * Navigate and wait for the SPA to hydrate from its public product API,
   * rather than an arbitrary sleep. Returns the API response so a test can
   * assert the UI against the same payload the UI itself rendered from.
   */
  async open(slug?: string): Promise<Response> {
    const [apiResponse] = await Promise.all([
      this.page.waitForResponse(
        (r) => r.url().includes(api.publicProduct(slug)) && r.request().method() === 'GET',
      ),
      this.page.goto(routes.product(slug), { waitUntil: 'domcontentloaded' }),
    ]);
    await expect(sel.productPage.talkToMe(this.page)).toBeVisible();
    return apiResponse;
  }

  async productPayload(slug?: string): Promise<unknown> {
    const res = await this.page.request.get(api.publicProduct(slug));
    expect(res.ok(), `public product API returned ${res.status()}`).toBeTruthy();
    return res.json();
  }

  async startVoiceSession(): Promise<void> {
    await sel.productPage.talkToMe(this.page).click();
  }

  async galleryCount(): Promise<number> {
    return sel.productPage.galleryThumbs(this.page).count();
  }

  /** Console errors collected for the current page - asserted by the smoke suite. */
  static collectConsoleErrors(page: Page): string[] {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    page.on('pageerror', (err) => errors.push(err.message));
    return errors;
  }
}
