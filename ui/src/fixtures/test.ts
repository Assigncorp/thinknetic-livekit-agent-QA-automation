import { test as base, expect } from '@playwright/test';
import { ProductPage } from '../pages/ProductPage.js';
import { VoiceWidget } from '../pages/VoiceWidget.js';
import { ChatWidget } from '../pages/ChatWidget.js';

type Fixtures = {
  productPage: ProductPage;
  voiceWidget: VoiceWidget;
  chatWidget: ChatWidget;
  /** Console + page errors captured for the whole test. */
  consoleErrors: string[];
  /** WebSocket URLs the page opened - used to detect the realtime connection. */
  socketUrls: string[];
};

export const test = base.extend<Fixtures>({
  consoleErrors: async ({ page }, use) => {
    await use(ProductPage.collectConsoleErrors(page));
  },
  socketUrls: async ({ page }, use) => {
    await use(VoiceWidget.trackWebSockets(page));
  },
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
