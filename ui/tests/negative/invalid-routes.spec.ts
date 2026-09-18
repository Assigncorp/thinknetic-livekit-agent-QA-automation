import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { testData } from '../../src/utils/testdata.js';

/**
 * Negative: the app must fail closed. A bad slug should never leave an agent
 * entry point on screen - that would let a user start a session against a
 * product with no knowledge base behind it.
 */
test.describe('@negative invalid routes', () => {
  for (const invalid of testData.invalidProducts().filter((p) => p.slug !== '')) {
    test(`no agent entry point for /${invalid.org}/products/${invalid.slug}`, async ({
      page,
      productPage,
    }) => {
      await productPage.openRaw(invalid.org, invalid.slug);
      await expect(sel.productPage.talkToMe(page)).toHaveCount(0);
    });
  }

  test('public API rejects unknown products with the documented error shape', async ({ page }) => {
    const res = await page.request.get(
      '/api/v1/public/organizations/e/products/definitely-not-a-real-product',
    );
    expect(res.status()).toBe(404);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body).toHaveProperty('message');
    expect(body).toHaveProperty('statusCode', 404);
  });
});
