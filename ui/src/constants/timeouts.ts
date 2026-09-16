/**
 * Every wait budget in one place. A magic number inside a test is a bug -
 * when a budget needs tuning it should be tuned once, here, with a comment
 * saying what it was based on.
 */
export const TIMEOUT = {
  /** Page navigation to DOMContentLoaded. */
  navigation: 30_000,
  /** A normal element appearing after hydration. */
  element: 10_000,
  /** The agent panel mounting after "Talk to me" is clicked. */
  widgetMount: 15_000,
  /** Reaching a connected/listening state. Placeholder - reset to ~p95 of a week of dev runs. */
  sessionConnect: 15_000,
  /** First agent reply in chat mode. LLM + TTS, so generous by design. */
  agentReply: 30_000,
} as const;

/**
 * Performance budgets asserted by tests. Separate from TIMEOUT: a timeout is
 * "give up here", a budget is "slower than this is a defect".
 */
export const BUDGET = {
  /** Observed ~0.4s on dev 2026-09-16. */
  apiResponseMs: 3_000,
  /** Click to connected state. Placeholder pending baseline data. */
  sessionConnectMs: 15_000,
} as const;
