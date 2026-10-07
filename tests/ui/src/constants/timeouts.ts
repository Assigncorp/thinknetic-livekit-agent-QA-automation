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
