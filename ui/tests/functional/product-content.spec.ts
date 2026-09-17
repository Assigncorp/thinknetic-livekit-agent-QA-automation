import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';

type ProductPayload = {
  name: string;
  slug: string;
  has_assistant: boolean;
  assets: unknown[];
};

/**
 * Functional: the rendered page agrees with the payload it was built from.
 * Using the API as the oracle keeps these assertions honest without hardcoding
 * copy that marketing will change next week.
 */
test.describe('@regression product content', () => {
  test('page shows the product name from the API', async ({ page, productPage }) => {
    await productPage.open();
    const payload = (await productPage.productPayload()) as ProductPayload;

    expect(payload.name, 'API returned no product name').toBeTruthy();
    await expect(page.getByText(payload.name, { exact: false }).first()).toBeVisible();
  });

  test('agent entry point matches the has_assistant flag', async ({ page, productPage }) => {
    await productPage.open();
    const payload = (await productPage.productPayload()) as ProductPayload;

    const expected = payload.has_assistant ? 1 : 0;
    await expect(sel.productPage.talkToMe(page)).toHaveCount(expected);
  });

  test('gallery renders an image for the assets in the payload', async ({ productPage }) => {
    await productPage.open();
    const payload = (await productPage.productPayload()) as ProductPayload;

    expect(payload.assets.length, 'API returned no assets').toBeGreaterThan(0);
    expect(await productPage.galleryCount()).toBeGreaterThan(0);
  });

  test('image lightbox opens and closes', async ({ page, productPage }) => {
    await productPage.open();
    await sel.productPage.expandPhoto(page).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();
  });
});
