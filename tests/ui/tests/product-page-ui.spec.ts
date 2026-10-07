import { expect, test } from '@playwright/test';
import { sel } from '../src/selectors.js';

const ORG = process.env.ORG_SLUG ?? 'e';
const PRODUCT = process.env.PRODUCT_SLUG ?? 'chip-spreader';
const PAGE_PATH = `/${ORG}/products/${PRODUCT}`;
const PRODUCT_API = `/api/v1/public/organizations/${ORG}/products/${PRODUCT}`;

const CALLER = {
  serial: process.env.TEST_SERIAL ?? 'K7170',
  name: process.env.TEST_CALLER_NAME ?? 'Dale Hutchins',
  company: process.env.TEST_CALLER_COMPANY ?? 'Fielder Paving',
  // Ten bare digits: the field drops anything else. 555-01xx is the fictional block.
  phone: process.env.TEST_CALLER_PHONE ?? '4805550142',
};

const SESSION_API = /\/assistant-session\b/;

type ProductPayload = { name: string; has_assistant: boolean; assets: unknown[] };

/** The LiveKit room named in a socket URL's access_token (a JWT), if any. */
function roomFromSocket(url: string): string | undefined {
  try {
    const jwt = new URL(url).searchParams.get('access_token');
    const body = jwt?.split('.')[1];
    if (!body) return undefined;
    const claims = JSON.parse(Buffer.from(body, 'base64url').toString('utf8')) as { video?: { room?: string } };
    return claims.video?.room;
  } catch {
    return undefined;
  }
}

/**
 * The whole product support page is present and in place, the caller form and
 * the page refuse what they should (the "negative:" steps), then "Talk to me"
 * really starts a call. The public product API the page hydrates from is the
 * oracle, so no marketing copy is hardcoded. The call is a real agent session
 * on the shared dev deployment, and it is hung up at the end.
 */
test('product support page: the whole UI is present, refuses bad input, and "Talk to me" starts a call', async ({ page, context }) => {
  test.setTimeout(120_000);
  const errors: string[] = [];
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', (e) => errors.push(e.message));
  const sockets: string[] = [];
  page.on('websocket', (ws) => {
    sockets.push(ws.url());
    // The call's reference: the LiveKit room is named in the access token on the socket URL.
    const room = roomFromSocket(ws.url());
    if (room && !test.info().annotations.some((a) => a.type === 'livekit-room' && a.description === room)) {
      test.info().annotations.push({ type: 'livekit-room', description: room });
      console.log(`[ui] call room: ${room}`);
    }
  });
  // Every attempt to start a call. A refused form must not add to this.
  let sessionRequests = 0;
  page.on('request', (r) => {
    if (SESSION_API.test(r.url()) && r.method() === 'POST') sessionRequests += 1;
  });

  /** Fills the form, submits it, and checks it was refused without trying to start a call. */
  const expectRefused = async (values: typeof CALLER, why: string, message?: RegExp) => {
    const before = sessionRequests;
    await form.serial(page).fill(values.serial);
    await form.name(page).fill(values.name);
    await form.company(page).fill(values.company);
    await form.phone(page).fill(values.phone);
    await form.startCall(page).click();
    if (message) await expect(form.dialog(page).getByText(message), `${why}: no error shown`).toBeVisible();
    await expect(form.dialog(page), `${why}: the form was accepted`).toBeVisible();
    expect(sessionRequests - before, `${why}: a call was attempted`).toBe(0);
  };

  let payload!: ProductPayload;
  const form = sel.callerIntake;
  const panel = sel.callPanel;

  await test.step('page loads from the public product API', async () => {
    const [apiResponse] = await Promise.all([
      page.waitForResponse((r) => r.url().includes(PRODUCT_API) && r.request().method() === 'GET'),
      page.goto(PAGE_PATH),
    ]);
    expect(apiResponse.status(), 'public product API status').toBe(200);
    payload = (await apiResponse.json()) as ProductPayload;
    expect(payload.name, 'API returned no product name').toBeTruthy();
  });

  await test.step('welcome dialog asks for the microphone, and "Enable microphone" closes it', async () => {
    const welcome = sel.welcome;
    await expect(welcome.dialog(page), 'no "Welcome!" dialog on load').toBeVisible();
    await expect(welcome.dialog(page).getByText(/allow microphone/i)).toBeVisible();
    await expect(welcome.notNow(page)).toBeEnabled();
    await expect(welcome.enableMic(page)).toBeEnabled();
    // What a user accepting the browser's permission prompt does.
    await context.grantPermissions(['microphone']);
    await welcome.enableMic(page).click();
    await expect(welcome.dialog(page), '"Enable microphone" did not close the welcome dialog').toBeHidden();
  });

  await test.step('header: title, heading, product name, assistant status', async () => {
    await expect(page).toHaveTitle(new RegExp(payload.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'));
    await expect(sel.productPage.heading(page)).toBeVisible();
    await expect(page.getByText(payload.name, { exact: false }).first()).toBeVisible();
    await expect(sel.productPage.assistantOnline(page)).toBeVisible();
  });

  await test.step('agent entry point matches has_assistant', async () => {
    expect(payload.has_assistant, 'API says this product has no assistant').toBe(true);
    await expect(sel.productPage.talkToMe(page)).toBeEnabled();
  });

  await test.step('gallery shows the product images', async () => {
    expect(payload.assets.length, 'API returned no assets').toBeGreaterThan(0);
    await expect(sel.productPage.galleryThumbs(page).first()).toBeVisible();
  });

  await test.step('photo lightbox opens and closes', async () => {
    await sel.productPage.expandPhoto(page).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();
  });

  await test.step('"Talk to me" opens the caller form with all four fields', async () => {
    await sel.productPage.talkToMe(page).click();
    await expect(form.dialog(page), '"Talk to me" did not open the "Before we start" form').toBeVisible();
    await expect(form.serial(page), 'no serial number field').toBeVisible();
    await expect(form.name(page), 'no caller name field').toBeVisible();
    await expect(form.company(page), 'no company name field').toBeVisible();
    await expect(form.phone(page), 'no phone number field').toBeVisible();
    await expect(form.startCall(page)).toBeEnabled();
    await expect(form.cancel(page)).toBeEnabled();
  });

  await test.step('negative: an empty form does not start a call', async () => {
    await expectRefused({ serial: '', name: '', company: '', phone: '' }, 'every field empty');
  });

  await test.step('negative: a form missing any one field does not start a call', async () => {
    for (const field of ['serial', 'name', 'company', 'phone'] as const) {
      await expectRefused({ ...CALLER, [field]: '' }, `${field} left empty`);
    }
  });

  await test.step('negative: a name of only spaces is refused', async () => {
    await expectRefused({ ...CALLER, name: '   ' }, 'blank name', /your name is required/i);
  });

  await test.step('negative: a phone number that is too short is refused', async () => {
    await expectRefused({ ...CALLER, phone: '48055' }, 'five-digit phone', /enter a valid phone number/i);
  });

  await test.step('negative: the phone field takes digits only, ten at most', async () => {
    const phone = form.phone(page);
    await phone.fill('');
    await phone.pressSequentially('abcdefghij');
    await expect(phone, 'letters were accepted in the phone number').toHaveValue('');
    await phone.fill('');
    await phone.pressSequentially('480555014299');
    await expect(phone, 'more than ten digits were accepted').toHaveValue('4805550142');
  });

  await test.step('Cancel closes the form', async () => {
    await form.cancel(page).click();
    await expect(form.dialog(page), 'Cancel did not close the form').toBeHidden();
  });

  await test.step('no console or page errors before the call', async () => {
    // Third-party noise (fonts, analytics, extensions) is not the app's.
    const ours = errors.filter((e) => !/favicon|fonts\.g|chrome-extension|ResizeObserver/i.test(e));
    expect(ours, `unexpected console errors:\n${ours.join('\n')}`).toHaveLength(0);
  });

  await test.step('negative: a call that cannot start tells the caller and offers "Start again"', async () => {
    // The session endpoint fails. Intercepted, so no agent session is used.
    await page.route(SESSION_API, (r) =>
      r.fulfill({ status: 500, contentType: 'application/json', body: '{"statusCode":500,"message":"Internal server error"}' }),
    );
    await sel.productPage.talkToMe(page).click();
    await form.serial(page).fill(CALLER.serial);
    await form.name(page).fill(CALLER.name);
    await form.company(page).fill(CALLER.company);
    await form.phone(page).fill(CALLER.phone);
    await form.startCall(page).click();
    await expect(page.getByRole('alert'), 'no error was shown to the caller').toContainText(/couldn.t start the call/i, {
      timeout: 15_000,
    });
    await expect(panel.startAgain(page)).toBeVisible();
    await expect(panel.end(page), 'a call panel is up for a call that never started').toBeHidden();

    // Back to a clean page for the real call.
    await page.unroute(SESSION_API);
    await page.reload();
    if (await sel.welcome.dialog(page).isVisible().catch(() => false)) await sel.welcome.enableMic(page).click();
    await expect(sel.productPage.talkToMe(page)).toBeEnabled();
  });

  await test.step('fill in the caller form and start the call', async () => {
    await sel.productPage.talkToMe(page).click();
    await expect(form.dialog(page)).toBeVisible();
    await form.serial(page).fill(CALLER.serial);
    await form.name(page).fill(CALLER.name);
    await form.company(page).fill(CALLER.company);
    await form.phone(page).fill(CALLER.phone);
    await form.startCall(page).click();
    await expect(form.dialog(page), 'the form did not accept the caller details').toBeHidden();
  });

  await test.step('the call connects over LiveKit', async () => {
    await expect(panel.end(page), 'no call panel opened').toBeVisible({ timeout: 20_000 });
    await expect(panel.live(page), 'the call never reached Listening/Thinking/Speaking').toBeVisible({
      timeout: 20_000,
    });
    expect(
      sockets.some((u) => /livekit/i.test(u)),
      `no LiveKit socket opened; sockets seen: ${sockets.join(', ') || 'none'}`,
    ).toBe(true);
  });

  await test.step('the agent greets the caller by name', async () => {
    const firstName = CALLER.name.split(' ')[0]!;
    await expect(page.getByText(new RegExp(`\\b${firstName}\\b`, 'i')).first(), 'no greeting from the agent').toBeVisible({
      timeout: 30_000,
    });
  });

  await test.step('the mic opens live and mutes on request', async () => {
    await expect(panel.mute(page), 'the call did not open with a live mic').toBeEnabled();
    await panel.mute(page).click();
    await expect(panel.unmute(page), 'the mic did not mute').toBeVisible();
  });

  await test.step('"End" hangs up', async () => {
    await panel.end(page).click();
    await expect(page.getByText(/call ended/i)).toBeVisible();
    await expect(panel.startAgain(page)).toBeVisible();
  });

  for (const [what, path] of [
    ['an unknown product', `/${ORG}/products/definitely-not-a-real-product`],
    ['an unknown organization', `/zz-not-an-org/products/${PRODUCT}`],
  ] as const) {
    await test.step(`negative: ${what} shows "Product not found" and no way to start a call`, async () => {
      await page.goto(path);
      await expect(page.getByText(/product not found/i)).toBeVisible();
      await expect(sel.productPage.talkToMe(page), `"Talk to me" offered for ${what}`).toHaveCount(0);
    });
  }
});
