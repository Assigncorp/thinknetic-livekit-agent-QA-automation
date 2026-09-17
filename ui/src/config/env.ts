/**
 * Single source of truth for environment-dependent values.
 * Nothing in tests or page objects should read process.env directly.
 *
 * Every value here is what changes when this suite is pointed at a different
 * product, so a new product is a new `.env`, not a code change.
 */
export const env = {
  baseUrl: process.env.BASE_URL ?? 'https://etnyre-dev.thinknetic.app',
  orgSlug: process.env.ORG_SLUG ?? 'e',
  productSlug: process.env.PRODUCT_SLUG ?? 'chip-spreader',
  /**
   * What the product page's title should contain. Defaults to the slug with
   * its hyphens removed, which is right whenever the title is just the product
   * name; set PRODUCT_TITLE when it is not.
   */
  productTitle: process.env.PRODUCT_TITLE ?? (process.env.PRODUCT_SLUG ?? 'chip-spreader').replace(/-/g, ' '),
  /** An org that does not exist, for the fail-closed checks. */
  unknownOrgSlug: process.env.UNKNOWN_ORG_SLUG ?? 'zz-not-an-org',
  /** A product that does not exist, for the fail-closed checks. */
  unknownProductSlug: process.env.UNKNOWN_PRODUCT_SLUG ?? 'definitely-not-a-real-product',
} as const;

/** Matches the product title case-insensitively, whitespace-tolerant. */
export const productTitlePattern = (): RegExp =>
  new RegExp(env.productTitle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g, '\\s*'), 'i');

export const routes = {
  /** Public product support page - the current system under test. */
  product: (slug: string = env.productSlug) => `/${env.orgSlug}/products/${slug}`,
} as const;

export const api = {
  /** Public product payload the SPA hydrates from. Useful as a test oracle. */
  publicProduct: (slug: string = env.productSlug) =>
    `/api/v1/public/organizations/${env.orgSlug}/products/${slug}`,
} as const;
