import { test, expect } from '../../src/fixtures/test.js';
import type { Request } from '@playwright/test';
import { sel } from '../../src/selectors.js';
import { testbed, callerDetails, resolveChatCase } from '../../src/config/testbed.js';
import {
  LiveKitServer,
  livekitServerAvailable,
  AGENT_KIND,
  STANDARD_KIND,
  MICROPHONE_SOURCE,
} from '../../src/utils/livekitServer.js';

/**
 * BLK: the browser's call, checked from the LiveKit server's side.
 *
 * The SDK suite (sdk/) owns the conversation and the knowledge-base verdict.
 * This spec owns what only a real browser can prove - that the page, with its
 * own WebRTC stack, mic permission and controls, produces the room it should:
 *
 *   BLK-01 the page asks for a session with exactly what the form collected
 *   BLK-02 the token it is given dispatches the verified agent worker
 *   BLK-03 the agent really joins the page's room (server view)
 *   BLK-04 the page publishes a microphone track, and "Mute" mutes it AT THE
 *          SFU - not just the icon (the hot mic on open is a known hazard)
 *   BLK-05 "End" removes the caller from the room and the agent leaves too
 *   BLK-06 a network drop mid-call either recovers or ends cleanly, never hangs
 *
 * Two sessions against the shared dev deployment, serial.
 */

const SDK = testbed.livekitSdk;
/** VERIFIED 2026-09-28 - read off a live session's dispatch; see judge.livekit._agentNameNote. */
const AGENT_NAME = testbed.judge.livekit.agentName;

test.describe.configure({ mode: 'serial' });

test.describe('@live @livekit browser call seen from the LiveKit server', () => {
  test.beforeEach(({}, testInfo) => {
    const why = livekitServerAvailable();
    test.skip(why !== null, `LiveKit server API unavailable: ${why}`);
    testInfo.setTimeout(testbed.budgets.sessionConnectMs + testbed.budgets.greetingMs + 120_000);
  });

  test('BLK-01..05 the page\'s room: request, dispatch, agent, mic mute at the SFU, clean hang-up', { tag: '@positive' }, async ({
    page,
    productPage,
    chatWidget,
    agentSession,
  }) => {
    const server = new LiveKitServer();
    const { serial } = resolveChatCase();
    const caller = callerDetails(serial.serial);

    let sessionRequest: Request | undefined;
    page.on('request', (req) => {
      if (/\/assistant-session\b/.test(req.url()) && req.method() === 'POST') sessionRequest = req;
    });
    const sessionResponse = page.waitForResponse((r) => /\/assistant-session\b/.test(r.url()));

    await productPage.open();
    await productPage.startVoiceSession(caller);
    const response = await sessionResponse;

    await test.step('BLK-01 the session request carries exactly what the form collected', async () => {
      expect(response.status()).toBe(200);
      expect(sessionRequest?.postDataJSON()).toEqual({
        serial_number: caller.serial,
        customer_name: caller.name,
        company_name: caller.company,
        phone: caller.phone,
      });
    });

    await test.step('BLK-02 the token dispatches the verified agent with the caller context', async () => {
      const body = (await response.json()) as { participant_token: string };
      const claims = JSON.parse(Buffer.from(body.participant_token.split('.')[1] ?? '', 'base64url').toString());
      const agents = claims.roomConfig?.agents ?? [];
      expect(agents.map((a: { agentName: string }) => a.agentName)).toEqual([AGENT_NAME]);
      expect(JSON.parse(agents[0].metadata).product_serial_number).toBe(caller.serial);
    });

    await chatWidget.expectOpen();
    const room = agentSession.room!;
    expect(room, 'the page never received a room').toBeTruthy();

    await test.step('BLK-03 the agent joins the page\'s room', async () => {
      const waited = await server.waitUntil(
        async () => (await server.participants(room)).some((p) => p.kind === AGENT_KIND),
        SDK.budgets.agentJoinMs + testbed.budgets.sessionConnectMs,
      );
      expect(waited, `no agent in ${room}`).not.toBeNull();
      const people = await server.participants(room);
      const agent = people.find((p) => p.kind === AGENT_KIND)!;
      expect(agent.attributes['lk.agent.name']).toBe(AGENT_NAME);
      expect(people.filter((p) => p.kind === STANDARD_KIND).map((p) => p.identity)).toEqual([agentSession.identity]);
    });

    await test.step('BLK-04 the page publishes a microphone, and Mute mutes it at the SFU', async () => {
      const micOf = async () =>
        (await server.participants(room))
          .find((p) => p.identity === agentSession.identity)
          ?.tracks.find((t) => t.source === MICROPHONE_SOURCE);

      const published = await server.waitUntil(async () => Boolean(await micOf()), 15_000);
      expect(published, 'the page never published a microphone track').not.toBeNull();
      const before = await micOf();
      test.info().annotations.push({ type: 'mic before mute', description: `muted=${before?.muted}` });
      console.log(`[BLK-04] server sees caller mic ${before?.sid} muted=${before?.muted} before Mute`);

      await chatWidget.muteMicrophone();
      const muted = await server.waitUntil(async () => (await micOf())?.muted === true, 10_000, 500);
      console.log(`[BLK-04] SFU reports the mic muted ${muted}ms after clicking Mute`);
      expect(
        muted,
        'the UI says the mic is muted, but the SFU still has the caller\'s microphone track live',
      ).not.toBeNull();
    });

    await test.step('BLK-05 End removes the caller, and the agent leaves the room', async () => {
      await chatWidget.end();
      const callerGone = await server.waitUntil(
        async () => !(await server.participants(room)).some((p) => p.identity === agentSession.identity),
        15_000,
      );
      expect(callerGone, 'the caller is still in the room after clicking End').not.toBeNull();
      const agentGone = await server.waitUntil(
        async () => !(await server.participants(room)).some((p) => p.kind === AGENT_KIND),
        SDK.budgets.agentLeavesAfterHangupMs,
      );
      test.info().annotations.push({ type: 'agent left after End', description: `${agentGone}ms` });
      console.log(`[BLK-05] caller left ${callerGone}ms after End; agent left ${agentGone}ms after that`);
      expect(agentGone, `the agent stayed in ${room} after the caller ended the call`).not.toBeNull();
    });
  });

  test('BLK-06 a network drop mid-call recovers or ends cleanly - it never hangs', { tag: '@edge' }, async ({
    page,
    context,
    productPage,
    chatWidget,
    agentSession,
  }) => {
    const server = new LiveKitServer();
    const { serial } = resolveChatCase();
    await productPage.open();
    await productPage.startVoiceSession(callerDetails(serial.serial));
    await chatWidget.expectOpen();
    await expect(sel.chatWidget.live(page)).toBeVisible({ timeout: testbed.budgets.sessionConnectMs });
    await chatWidget.muteMicrophone();
    const room = agentSession.room!;

    await context.setOffline(true);
    await page.waitForTimeout(8_000);
    await context.setOffline(false);

    // Either the call is usable again - the caller is back in the room - or
    // the page has said the call is over. Anything else inside 45s is a hang.
    const outcome = await Promise.race([
      server
        .waitUntil(async () => (await server.participants(room)).some((p) => p.identity === agentSession.identity), 45_000)
        .then((ms) => (ms === null ? 'hung' : 'recovered')),
      expect(sel.productPage.startAgain(page))
        .toBeVisible({ timeout: 45_000 })
        .then(() => 'ended'),
    ]).catch(() => 'hung');
    test.info().annotations.push({ type: 'after 8s offline', description: outcome });
    console.log(`[BLK-06] after 8s offline the call ${outcome}`);

    if (outcome === 'recovered') {
      await expect(sel.chatWidget.input(page)).toBeEnabled({ timeout: 15_000 });
    }
    expect(outcome, 'after the network came back the call neither recovered nor ended').not.toBe('hung');
    await chatWidget.end();
  });
});
