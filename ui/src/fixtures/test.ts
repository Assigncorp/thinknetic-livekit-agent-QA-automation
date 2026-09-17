import { test as base, expect } from '@playwright/test';
import { ProductPage } from '../pages/ProductPage.js';
import { VoiceWidget } from '../pages/VoiceWidget.js';
import { ChatWidget } from '../pages/ChatWidget.js';
import { trackAgentSession, describeSession, type AgentSessionRef } from '../utils/session.js';

type Fixtures = {
  productPage: ProductPage;
  voiceWidget: VoiceWidget;
  chatWidget: ChatWidget;
  /** Console + page errors captured for the whole test. */
  consoleErrors: string[];
  /** WebSocket URLs the page opened - used to detect the realtime connection. */
  socketUrls: string[];
  /** The LiveKit room this test's call ran in. Attached to every failure. */
  agentSession: AgentSessionRef;
};

export const test = base.extend<Fixtures>({
  consoleErrors: async ({ page }, use) => {
    await use(ProductPage.collectConsoleErrors(page));
  },
  socketUrls: async ({ page }, use) => {
    await use(VoiceWidget.trackWebSockets(page));
  },

  /**
   * Records which call a test actually ran, and hands that reference to
   * anything investigating a failure.
   *
   * `auto` on purpose: a test should not have to remember to ask for this.
   * Any failure in any live test is one somebody will want to trace back to a
   * specific call, and by then it is too late to start capturing. Tests that
   * never open a session simply record nothing.
   */
  agentSession: [
    async ({ page }, use, testInfo) => {
      const session = trackAgentSession(page);

      await use(session);

      if (!session.room) return;

      testInfo.annotations.push({ type: 'room', description: session.room });

      if (testInfo.status !== testInfo.expectedStatus) {
        await testInfo.attach('call reference', {
          body:
            `This run failed. The call it failed on:\n\n${describeSession(session)}\n\n` +
            `Quote the room when reporting it - it identifies this call exactly.`,
          contentType: 'text/plain',
        });
      }
    },
    { auto: true },
  ],

  productPage: async ({ page, consoleErrors }, use) => {
    void consoleErrors; // ensure listeners attach before navigation
    await use(new ProductPage(page));
  },
  voiceWidget: async ({ page }, use) => {
    await use(new VoiceWidget(page));
  },
  chatWidget: async ({ page }, use) => {
    await use(new ChatWidget(page));
  },
});

export { expect };
