import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { env, productTitlePattern, routes } from '../../src/config/env.js';

/**
 * Smoke: the page loads, hydrates and exposes its entry point.
 * If this is red, nothing else is worth running.
 */
test.describe('@smoke product support page', () => {
  test('loads and renders the agent entry point', async ({ page, productPage }) => {
    const apiResponse = await productPage.open();

    expect(apiResponse.status(), 'public product API status').toBe(200);
    await expect(page).toHaveTitle(productTitlePattern());
    await expect(sel.productPage.talkToMe(page)).toBeEnabled();
  });

  test('renders without console or page errors', async ({ productPage, consoleErrors }) => {
    await productPage.open();

    // Third-party noise (fonts, analytics, browser extensions) is not ours to fix.
    const ours = consoleErrors.filter(
      (e) => !/favicon|fonts\.g|chrome-extension|ResizeObserver/i.test(e),
    );
    expect(ours, `unexpected console errors:\n${ours.join('\n')}`).toHaveLength(0);
  });

  test('unknown product slug does not render an agent entry point', async ({ page }) => {
    await page.goto(routes.product(env.unknownProductSlug), { waitUntil: 'domcontentloaded' });
    await expect(sel.productPage.talkToMe(page)).toHaveCount(0);
  });
});
