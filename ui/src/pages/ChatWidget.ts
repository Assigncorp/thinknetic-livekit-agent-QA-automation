import { expect, type Page } from '@playwright/test';
import { sel } from '../selectors.js';
import { testbed, anyOf } from '../config/testbed.js';
import type { TranscriptMessage } from '../types/testbed.js';
import { BasePage } from './BasePage.js';

/** Values a configured reply may interpolate. */
export interface ConversationVars {
  serial: string;
  question: string;
  /** Answer to the agent's own follow-up questions. */
  clarification: string;
  /** Score to give if the agent asks the caller to rate the call. */
  feedback: string;
}

/** One turn the agent took, how it was understood, and what was said back. */
export interface ConversationStep {
  /** Matching `chatFlow.intents` id, or 'answer' / 'unrecognised'. */
  intent: string;
  agentTurn: string;
  reply: string | null;
  /** How long this turn took to arrive and finish streaming. */
  ms: number;
}

/** Fills {{serial}} / {{question}} / {{feedback}} in a configured reply. */
function render(template: string, vars: ConversationVars): string {
  return template.replace(
    /\{\{(\w+)\}\}/g,
    (whole, key: string) => vars[key as keyof ConversationVars] ?? whole,
  );
}

/** Turns already accounted for, keyed by text with a count (turns can legitimately repeat). */
function countTurns(turns: string[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const t of turns) counts.set(t, (counts.get(t) ?? 0) + 1);
  return counts;
}

/**
 * Turns in `current` beyond what `seen` already accounts for, matched by
 * position/count rather than plain text membership - so a turn the agent
 * legitimately repeats verbatim (a retry, a canned line) still counts as new
 * once it appears more times than it did in `seen`.
 */
function freshTurns(current: string[], seen: Map<string, number>): string[] {
  const remaining = new Map(seen);
  const fresh: string[] = [];
  for (const t of current) {
    const left = remaining.get(t) ?? 0;
    if (left > 0) {
      remaining.set(t, left - 1);
    } else {
      fresh.push(t);
    }
  }
  return fresh;
}

/**
 * The agent session panel, driven in TEXT (chat) mode.
 *
 * Reading the transcript
 * ---------------------
 * The transcript carries no roles, no test ids and hashed MUI class names, so
 * there is nothing stable to target with a CSS locator. What IS stable is the
 * layout contract: the agent's turns are left-aligned, the caller's are
 * right-aligned. So the reader runs in the page, walks the message stack and
 * infers the speaker from computed style. Uglier than a `[data-role]` attribute
 * and considerably more durable than a hashed class name.
 *
 * Holding a conversation
 * ----------------------
 * Nothing is ever typed while the agent is mid-sentence: turns stream token by
 * token, and the app silently drops anything sent before one finishes. Every
 * turn is read to completion, matched against `chatFlow.intents`, and answered
 * on its own terms - see `converse()`.
 */
export class ChatWidget extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // ---------------------------------------------------------------- lifecycle

  async expectOpen(): Promise<void> {
    await expect(sel.chatWidget.input(this.page)).toBeVisible({
      timeout: testbed.budgets.sessionConnectMs,
    });
    await expect(sel.chatWidget.send(this.page)).toBeVisible();
    await expect(sel.chatWidget.end(this.page)).toBeVisible();
  }

  /**
   * Mutes the caller's microphone and proves it took effect.
   *
   * A session does not open muted. The control is disabled while connecting,
   * then becomes enabled reading "Mute" - it is *offering* to mute, which means
   * audio is already going up. In text mode that lets room noise reach the
   * agent and steer the very conversation the suite is trying to drive, so
   * every session mutes before a word is typed.
   *
   * Verified on etnyre-dev 2026-09-17: disabled "Unmute" on open, enabled
   * "Mute" within about a second, "Unmute" again once clicked.
   */
  async muteMicrophone(): Promise<void> {
    const mute = sel.chatWidget.mute(this.page);
    await expect(
      mute,
      'the microphone control never became usable, so the mic may still be live',
    ).toBeEnabled({ timeout: testbed.budgets.sessionConnectMs });

    await mute.click();

    await expect(
      sel.chatWidget.unmute(this.page),
      'microphone did not mute - the control is still offering "Mute", so audio is going up',
    ).toBeVisible({ timeout: 10_000 });
  }

  /** Is the caller's microphone currently muted? */
  async isMicrophoneMuted(): Promise<boolean> {
    return sel.chatWidget.unmute(this.page).isVisible().catch(() => false);
  }

  async end(): Promise<void> {
    const btn = sel.chatWidget.end(this.page);
    if (await btn.isVisible().catch(() => false)) await btn.click();
  }

  // ------------------------------------------------------------- transcript

  /**
   * Every turn currently rendered, oldest first.
   *
   * Verified against etnyre-dev's actual DOM: a page-wide "most children
   * wins" search over every `.MuiStack-root` is not reliable - the page
   * banner and an in-panel "Listening — go ahead" status pill are also
   * multi-child Stacks that can equal or beat the real transcript's child
   * count early in a conversation, and silently win.
   *
   * What IS reliable: the message area is the input row's nearest preceding
   * sibling with any text in it (skipping the empty divider between them), and
   * inside it the message list is whichever element has the most `.MuiStack-root`
   * children - the turns are its direct children.
   *
   * Taking the list's children, rather than hunting for individual bubbles
   * further down, is what keeps a multi-part message together. An answer can
   * arrive as a captioned diagram PLUS text ("Display shows left and right
   * auger speeds" + "That Invalid Speed fault can be frustrating..."), and
   * descending past the list splits that into two turns, hands back the
   * caption as the answer, and leaves the still-streaming text unwatched.
   */
  async transcript(): Promise<TranscriptMessage[]> {
    // The reader is anchored on the input box, which the app removes when the
    // call ends. Without this, every read after that point waits out its
    // locator timeout and reports a missing textbox - true, but useless. The
    // session ending mid-conversation is the thing worth saying.
    if (await sel.productPage.startAgain(this.page).isVisible().catch(() => false)) {
      throw new Error(
        'The agent session ended before the conversation finished - the panel is ' +
          'showing "Call ended" and "Start again". The transcript cannot be read ' +
          'any more. Usually the agent hung up after its idle prompts went ' +
          'unanswered, so check what the suite last said to it.',
      );
    }

    return sel.chatWidget.input(this.page).evaluate((inputEl) => {
      const inputRow = (inputEl as HTMLElement).closest('.MuiStack-root');
      let messageArea = inputRow?.previousElementSibling as HTMLElement | null;
      while (messageArea && !messageArea.innerText.trim()) {
        messageArea = messageArea.previousElementSibling as HTMLElement | null;
      }
      if (!messageArea) return [];

      const stackChildren = (el: Element): HTMLElement[] =>
        Array.from(el.children).filter((c) =>
          c.classList.contains('MuiStack-root'),
        ) as HTMLElement[];

      // Breadth-first, so ties resolve to the shallowest candidate: with a
      // single message every level has one stack child, and the outermost is
      // the one that still holds the whole message.
      let list = messageArea;
      let best = stackChildren(messageArea).length;
      const queue: HTMLElement[] = [...stackChildren(messageArea)];
      while (queue.length > 0) {
        const el = queue.shift()!;
        const count = stackChildren(el).length;
        if (count > best) {
          best = count;
          list = el;
        }
        queue.push(...stackChildren(el));
      }
      if (best === 0) return [];

      return stackChildren(list)
        .map((el) => {
          const style = window.getComputedStyle(el);
          const rightAligned =
            style.alignItems === 'flex-end' || style.justifyContent === 'flex-end';
          return { who: rightAligned ? 'user' : 'agent', text: el.innerText.trim() };
        })
        .filter((m) => m.text.length > 0) as TranscriptMessage[];
    });
  }

  /**
   * Agent turns only, with the unprompted idle nudges removed.
   *
   * The agent injects "Are you still there?" on its own while waiting, so any
   * assertion anchored on "the last message" or on a message count is flaky
   * unless those are filtered out first.
   */
  async agentTurns(): Promise<string[]> {
    const idle = anyOf(testbed.chatFlow.agentIdlePrompts);
    return (await this.transcript())
      .filter((m) => m.who === 'agent' && !idle.test(m.text))
      .map((m) => m.text);
  }

  async lastAgentTurn(): Promise<string> {
    const turns = await this.agentTurns();
    return turns.at(-1) ?? '';
  }

  // ------------------------------------------------------------------ actions

  /**
   * Waits until the newest agent turn stops growing.
   *
   * Turns stream in token by token, so a pattern match like /serial number/
   * lands while the agent is still mid-sentence. Sending at that moment gets
   * the message dropped by the app: verified on etnyre-dev 2026-09-17, where a
   * serial sent mid-stream was ignored and the agent asked for it again, while
   * the identical serial sent once the agent had gone quiet was read back
   * immediately.
   */
  async waitForQuiet(
    quietMs = testbed.chatFlow.turnQuietMs,
    timeoutMs = 25_000,
  ): Promise<void> {
    let previous = '';
    let unchangedSince = Date.now();

    try {
      await expect
        .poll(
          async () => {
            const current = await this.lastAgentTurn();
            if (current !== previous) {
              previous = current;
              unchangedSince = Date.now();
            }
            return Date.now() - unchangedSince;
          },
          { timeout: timeoutMs, intervals: [200, 200, 300, 500] },
        )
        .toBeGreaterThanOrEqual(quietMs);
    } catch {
      // Never went quiet inside the window. Proceed and let the caller's own
      // budget assertion be the thing that fails, not this helper.
    }
  }

  /**
   * Sends a message and returns the agent turns as they stood the instant it
   * went out - the only correct baseline for "what did the agent say back".
   *
   * Snapshotting before the quiet wait instead would misattribute any turn
   * that lands during that wait as a reply to this message. That is not
   * hypothetical: it made the agent's "I've got your machine pulled up, what
   * can I help you with?" turn get read as the answer to the question that had
   * not been sent yet.
   */
  async send(message: string): Promise<string[]> {
    await this.waitForQuiet();
    const before = await this.agentTurns();
    const input = sel.chatWidget.input(this.page);
    await input.fill(message);
    await sel.chatWidget.send(this.page).click();
    // The input clearing is the app's own acknowledgement that it took the turn.
    await expect(input).toHaveValue('', { timeout: 10_000 });
    return before;
  }

  /**
   * Drives the conversation by reacting to the agent, rather than replaying a
   * fixed script.
   *
   * The agent is not deterministic. It re-asks for a serial it dropped, asks a
   * clarifying question instead of answering, opens with a summary of a
   * previous session, or volunteers an idle nudge. A fixed send-order gets out
   * of step with all of that and then asserts against the wrong turn.
   *
   * So: wait for each turn to FINISH streaming, read it, match it against
   * `chatFlow.intents`, and send whatever that intent calls for. Nothing is
   * ever typed until the agent has actually finished speaking.
   *
   * Returns every step taken, so the caller can assert on the timing and
   * ordering of the turns it cares about.
   */
  async converse(
    vars: ConversationVars,
    opts: {
      turnTimeoutMs: number;
      stopAfterIntent?: string;
      maxTurns?: number;
      maxClarifications?: number;
    },
  ): Promise<{ steps: ConversationStep[]; answer: string; fullAnswer: string }> {
    const { intents } = testbed.chatFlow;
    const maxTurns = opts.maxTurns ?? testbed.chatFlow.maxTurns;
    const maxClarifications = opts.maxClarifications ?? testbed.chatFlow.maxClarifications;
    const steps: ConversationStep[] = [];

    // Everything the agent says once our question is out. The agent walks a
    // procedure one step at a time, so the facts worth checking are spread
    // across several turns rather than sitting in any single one.
    const answerTurns: string[] = [];

    // Nothing has been acted on yet, so the greeting counts as unread even
    // though it is already on screen. Snapshotting the transcript here instead
    // marks it as seen and waits for a turn that never comes: the agent sits
    // through its idle nudges and hangs up, and the suite blames the app.
    let seen: string[] = [];
    let asked = false;
    let clarificationsSent = 0;

    for (let i = 0; i < maxTurns; i += 1) {
      const started = Date.now();
      const turn = await this.waitForNewAgentTurn(seen, opts.turnTimeoutMs);
      const ms = Date.now() - started;
      let intent = intents.find((candidate) => anyOf(candidate.match).test(turn));

      // The agent troubleshoots rather than answering outright, and phrases its
      // follow-ups freely ("Is this a new issue, or has it been happening for a
      // while?"). No phrase list keeps up with that, but the shape does: a turn
      // that ends in a question mark is asking us something, not answering.
      // Answer it from the contract and keep listening, up to a limit so a
      // dialogue that never lands still fails rather than looping.
      if (asked && !intent && /\?\s*$/.test(turn) && clarificationsSent < maxClarifications) {
        clarificationsSent += 1;
        intent = intents.find((candidate) => candidate.id === 'clarifying');
      }

      if (asked) answerTurns.push(turn);

      // Once our question is out, the first turn that is not one of the
      // conversational control turns is the agent finishing its answer.
      if (asked && !intent) {
        steps.push({ intent: 'answer', agentTurn: turn, reply: null, ms });
        return { steps, answer: turn, fullAnswer: answerTurns.join('\n') };
      }

      steps.push({
        intent: intent?.id ?? 'unrecognised',
        agentTurn: turn,
        reply: intent?.reply ? render(intent.reply, vars) : null,
        ms,
      });

      if (intent && opts.stopAfterIntent === intent.id) {
        return { steps, answer: '', fullAnswer: '' };
      }

      const reply = steps[steps.length - 1]!.reply;
      if (reply === null) {
        seen = [...seen, turn];
        continue;
      }

      seen = await this.send(reply);
      if (intent?.reply === '{{question}}') asked = true;
    }

    // Out of turns. If the question was asked and the agent has been talking,
    // that is an answer delivered across more steps than we were willing to
    // walk - hand back what it said rather than throwing away the evidence.
    if (asked && answerTurns.length > 0) {
      // Record it as the answer step too. Callers look for that step to time
      // the reply, and returning an answer without one crashes them.
      const last = answerTurns[answerTurns.length - 1]!;
      steps.push({
        intent: 'answer',
        agentTurn: last,
        reply: null,
        ms: steps[steps.length - 1]?.ms ?? 0,
      });
      return { steps, answer: last, fullAnswer: answerTurns.join('\n') };
    }

    throw new Error(
      `Conversation never reached the question in ${maxTurns} turns. Steps:\n` +
        steps.map((s) => `  [${s.intent}] ${s.agentTurn}`).join('\n'),
    );
  }

  /**
   * Handles whatever the agent says on the way out, then stops as soon as it
   * goes quiet. Used to answer a feedback request before hanging up.
   *
   * `only` is a whitelist of intent ids on purpose: the agent's closing turn is
   * often "anything else I can help with?", which matches `readyForQuestion`
   * and would otherwise re-ask the question we have already had answered.
   *
   * Returns the steps taken, empty if the agent had nothing more to say -
   * which, so far, is every recorded session.
   */
  async wrapUp(
    vars: ConversationVars,
    opts: { turnTimeoutMs: number; only: string[]; maxTurns?: number },
  ): Promise<ConversationStep[]> {
    const { intents } = testbed.chatFlow;
    const steps: ConversationStep[] = [];
    let seen = await this.agentTurns();

    for (let i = 0; i < (opts.maxTurns ?? 3); i += 1) {
      const started = Date.now();
      const turn = await this.nextAgentTurn(seen, opts.turnTimeoutMs);
      if (turn === null) break;

      const ms = Date.now() - started;
      const intent = intents.find((candidate) => anyOf(candidate.match).test(turn));
      const actionable = intent && opts.only.includes(intent.id) && intent.reply;
      const reply = actionable ? render(intent.reply!, vars) : null;

      steps.push({ intent: intent?.id ?? 'unrecognised', agentTurn: turn, reply, ms });

      if (reply === null) {
        seen = [...seen, turn];
        continue;
      }
      seen = await this.send(reply);
    }

    return steps;
  }

  /** Like waitForNewAgentTurn, but returns null instead of throwing on timeout. */
  private async nextAgentTurn(seen: string[], timeoutMs: number): Promise<string | null> {
    try {
      return await this.waitForNewAgentTurn(seen, timeoutMs);
    } catch {
      return null;
    }
  }

  /**
   * Waits for an agent turn matching `pattern` that was not already present.
   * Returns how long it took, in ms - the number the latency budget asserts on.
   */
  async waitForAgent(pattern: RegExp, timeoutMs: number, ignore: string[] = []): Promise<number> {
    const started = Date.now();
    const seen = countTurns(ignore);

    try {
      await expect
        .poll(
          async () => freshTurns(await this.agentTurns(), seen).some((t) => pattern.test(t)),
          { timeout: timeoutMs, intervals: [500, 1000, 1000, 2000] },
        )
        .toBe(true);
    } catch (err) {
      // Captured now, at actual timeout time - not when the poll started.
      const transcript = (await this.agentTurns()).join('\n');
      throw new Error(
        `No new agent turn matched ${pattern}. Transcript so far:\n${transcript}\n\n${(err as Error).message}`,
      );
    }

    return Date.now() - started;
  }

  /**
   * Waits for any new agent turn beyond the ones already seen, and returns it
   * complete.
   *
   * A turn is rendered while it is still streaming, so the moment one appears
   * it may be only its opening words - "The fan valve" is the start of "The
   * fan valve pressure is set to ...". Returning that would have assertions
   * judge a fragment, so the turn is allowed to finish before it is handed
   * back.
   */
  async waitForNewAgentTurn(alreadySeen: string[], timeoutMs: number): Promise<string> {
    const seen = countTurns(alreadySeen);
    let found = '';

    try {
      await expect
        .poll(
          async () => {
            const fresh = freshTurns(await this.agentTurns(), seen);
            found = fresh.at(-1) ?? '';
            return found.length;
          },
          { timeout: timeoutMs, intervals: [1000, 1000, 2000, 2000] },
        )
        .toBeGreaterThan(0);
    } catch (err) {
      const transcript = (await this.agentTurns()).join('\n');
      throw new Error(
        `Agent did not produce a new turn within budget. Transcript so far:\n${transcript}\n\n${(err as Error).message}`,
      );
    }

    await this.waitForQuiet();
    return freshTurns(await this.agentTurns(), seen).at(-1) ?? found;
  }
}
