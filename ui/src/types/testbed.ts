/** Types for config/testbed.config.json and resources/generated/*. */

export interface KnowledgeBase {
  id: string;
  file: string;
  machine: string;
  controller: string | null;
  hopperType: string | null;
  anchorSerial: string | null;
  enabled: boolean;
}

export interface SerialEntry {
  serial: string;
  description: string;
  controller: string;
  hopperType: string;
  sheet: string;
  kbId: string;
}

export interface Scenario {
  id: string;
  kbId: string;
  kind: 'faq' | 'howto' | 'problem';
  section: string;
  question: string;
  expectAnchors: string[];
  sourceLine: number;
}

/**
 * One thing the agent can ask for, and what to say back.
 * `reply` may contain {{serial}} / {{question}}; null means send nothing.
 */
export interface ChatIntent {
  id: string;
  match: string[];
  reply: string | null;
}

export interface TestbedConfig {
  resources: { root: string; kbDir: string; serialWorkbook: string; generatedDir: string };
  knowledgeBases: KnowledgeBase[];
  scenarioSelection: {
    mode: 'random' | 'fixed' | 'roundRobin';
    seed: number | null;
    fixedScenarioId: string | null;
    rotateSerials: boolean;
    serialsPerKb: number;
    excludeSerials: string[];
  };
  chatFlow: {
    agentIdlePrompts: string[];
    intents: ChatIntent[];
    /** Mute the caller's mic once the session connects; it opens live. */
    muteMicOnStart: boolean;
    /** How long a turn must stop changing before it counts as finished. */
    turnQuietMs: number;
    /** Upper bound on agent turns in one call. */
    maxTurns: number;
    /** How many agent follow-up questions to answer before giving up. */
    maxClarifications: number;
    clarificationReply: string;
    feedbackScale: { min: number; max: number };
  };
  budgets: {
    sessionConnectMs: number;
    greetingMs: number;
    serialAcknowledgedMs: number;
    answerMs: number;
    wrapUpMs: number;
    apiResponseMs: number;
  };
  assertions: {
    requireNonEmptyReply: boolean;
    /** The agent must ask the caller to rate the call before it ends. */
    requireFeedbackRequest: boolean;
    minReplyChars: number;
    checkExpectedAnchors: boolean;
    failOnWrongControllerFamily: boolean;
  };
}

/** One resolved test case: which serial to give, and what to ask once accepted. */
export interface ChatCase {
  scenario: Scenario;
  serial: SerialEntry;
  kb: KnowledgeBase;
}

/** A single turn as rendered in the transcript. */
export interface TranscriptMessage {
  who: 'agent' | 'user';
  text: string;
}
