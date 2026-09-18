import { expect, type Page, type Response } from '@playwright/test';
import { sel } from '../selectors.js';
import { api, routes } from '../config/env.js';
import { TIMEOUT } from '../constants/timeouts.js';
import type { ProductPayload } from '../types/product.js';
import type { CallerDetails } from '../types/testbed.js';
import { BasePage } from './BasePage.js';

/**
 * The public product support page - entry point for both voice and chat modes.
 */
export class ProductPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate and wait for the SPA to hydrate from its public product API,
   * rather than an arbitrary sleep. Returns the API response so a test can
   * assert the UI against the same payload the UI itself rendered from.
   */
  async open(slug?: string): Promise<Response> {
    const [apiResponse] = await Promise.all([
      this.page.waitForResponse(
        (r) => r.url().includes(api.publicProduct(slug)) && r.request().method() === 'GET',
        { timeout: TIMEOUT.navigation },
      ),
      this.goto(routes.product(slug)),
    ]);
    await expect(sel.productPage.talkToMe(this.page)).toBeVisible({ timeout: TIMEOUT.element });
    return apiResponse;
  }

  /** Opens a page without requiring the agent entry point - for negative cases. */
  async openRaw(orgSlug: string, productSlug: string): Promise<void> {
    await this.goto(`/${orgSlug}/products/${productSlug}`);
  }

  async productPayload(slug?: string): Promise<ProductPayload> {
    const res = await this.page.request.get(api.publicProduct(slug));
    expect(res.ok(), `public product API returned ${res.status()}`).toBeTruthy();
    return (await res.json()) as ProductPayload;
  }

  /**
   * Opens the "Before we start" form without filling it.
   *
   * VERIFIED 2026-09-18: "Talk to me" no longer starts a call. It opens a
   * dialog asking for the serial number, the caller's name, their company and
   * a phone number - all four required - and the call begins on "Start call".
   */
  async openCallerForm(): Promise<void> {
    await sel.productPage.talkToMe(this.page).click();
    await expect(
      sel.callerIntake.dialog(this.page),
      'clicking "Talk to me" did not open the "Before we start" form',
    ).toBeVisible({ timeout: TIMEOUT.element });
  }

  /**
   * Fills the caller details in and starts the call.
   *
   * The dialog closing is the app's own acknowledgement that it accepted the
   * details: a field it rejects keeps the form open and flags itself instead.
   * That distinction is worth spelling out in the failure, because the phone
   * validator is strict enough to refuse the placeholder the field itself
   * suggests - so a rejected value looks exactly like a call that never
   * started unless the form's own complaint is read back.
   */
  async startVoiceSession(caller: CallerDetails): Promise<void> {
    await this.openCallerForm();

    const form = sel.callerIntake;
    await form.serial(this.page).fill(caller.serial);
    await form.name(this.page).fill(caller.name);
    await form.company(this.page).fill(caller.company);
    await form.phone(this.page).fill(caller.phone);
    await form.startCall(this.page).click();

    try {
      await expect(form.dialog(this.page)).toBeHidden({ timeout: TIMEOUT.element });
    } catch {
      const complaints = (await form.fieldErrors(this.page).allInnerTexts())
        .map((t) => t.trim())
        .filter(Boolean);
      throw new Error(
        'The "Before we start" form did not accept the caller details, so no call was ' +
          `started. It is still open, saying: ${complaints.join(' | ') || '(nothing)'}\n` +
          `serial: ${caller.serial}\nname: ${caller.name}\n` +
          `company: ${caller.company}\nphone: ${caller.phone}`,
      );
    }
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
