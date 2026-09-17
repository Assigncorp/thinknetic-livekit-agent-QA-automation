import type { Page } from '@playwright/test';

/**
 * The identity of one agent call, for quoting in a bug report.
 *
 * Every session start returns a LiveKit room name unique to that call, so it
 * is the reference that ties a failing run to what actually happened on the
 * backend - far more useful than a timestamp, and it needs no access to the
 * (login-walled) call-logs page.
 */
export interface AgentSessionRef {
  /**
   * The call's reference number, as the product calls it - a LiveKit room SID
   * like `RM_jxf8hr3qpAiT`. This is the value to quote in a bug report.
   *
   * It is NOT in the session API response or the DOM: the SID is assigned by
   * LiveKit when the room is created, and only reaches the browser inside the
   * signalling frames, so it is read from there.
   */
  referenceNumber: string | null;
  /** LiveKit room for this call, e.g. `product-<productId>-<callId>`. */
  room: string | null;
  /**
   * The per-call UUID inside the room name.
   *
   * The room is `product-<productId>-<callId>`, and the product half matches
   * the `id` from the public product endpoint - so this trailing UUID is what
   * identifies the call itself. Both forms are recorded because the call-logs
   * page (which is behind a login, so unverified) may label either one the
   * "reference number".
   */
  callId: string | null;
  /** The caller's participant identity in that room. */
  identity: string | null;
  /** The LiveKit server the call ran on. */
  serverUrl: string | null;
}

/**
 * Reads the room out of a LiveKit participant token.
 *
 * The token is a JWT, so its payload is readable without any secret. ONLY the
 * room and identity are taken: the token itself is a live credential that
 * grants joining the call, and it must never reach a log, a report or a
 * screenshot.
 */
export function roomFromParticipantToken(token: string): {
  room: string | null;
  identity: string | null;
} {
  try {
    const [, payload] = token.split('.');
    if (!payload) return { room: null, identity: null };

    const claims = JSON.parse(Buffer.from(payload, 'base64url').toString()) as {
      video?: { room?: string };
      roomConfig?: { name?: string };
      sub?: string;
    };

    return {
      room: claims.video?.room ?? claims.roomConfig?.name ?? null,
      identity: claims.sub ?? null,
    };
  } catch {
    // A token we cannot read is not worth failing a test over - the caller
    // reports "unknown" and the run carries on.
    return { room: null, identity: null };
  }
}

/**
 * Watches for the call the page opens and records its room.
 *
 * Returns immediately with an object that fills in once the session starts, so
 * it can be set up before navigation and read afterwards.
 */
export function trackAgentSession(page: Page): AgentSessionRef {
  const ref: AgentSessionRef = {
    referenceNumber: null,
    room: null,
    callId: null,
    identity: null,
    serverUrl: null,
  };

  // The reference number arrives over the realtime socket, not over HTTP.
  // Frames are protobuf, but a SID is an ASCII string inside them, so the
  // first RM_ token in the stream is the room this call was given. Reading it
  // this way avoids pulling in a protobuf decoder for one field.
  page.on('websocket', (ws) => {
    ws.on('framereceived', (frame) => {
      if (ref.referenceNumber) return;
      const payload = frame.payload;
      const text = typeof payload === 'string' ? payload : payload.toString('latin1');
      ref.referenceNumber = /\b(RM_[A-Za-z0-9]{8,})/.exec(text)?.[1] ?? null;
    });
  });

  page.on('response', (response) => {
    if (!/\/assistant-session\b/.test(response.url())) return;

    void response
      .json()
      .then((body: { server_url?: string; participant_token?: string }) => {
        ref.serverUrl = body.server_url ?? null;
        if (!body.participant_token) return;
        const { room, identity } = roomFromParticipantToken(body.participant_token);
        ref.room = room;
        ref.callId = callIdFromRoom(room);
        ref.identity = identity;
      })
      .catch(() => {
        // Body unreadable (redirect, abort, non-JSON). Nothing to record.
      });
  });

  return ref;
}

/** Splits `product-<productId>-<callId>` into its two UUIDs. */
export function callIdFromRoom(room: string | null): string | null {
  if (!room) return null;
  const match = /^product-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}-([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/i.exec(
    room,
  );
  return match?.[1] ?? null;
}

/** One-line description for a report or a bug ticket. */
export function describeSession(ref: AgentSessionRef): string {
  if (!ref.room && !ref.referenceNumber) {
    return 'reference: (not captured - the session never started)';
  }
  return [
    `Ref #:    ${ref.referenceNumber ?? '(not seen in signalling)'}`,
    `room:     ${ref.room}`,
    `call id:  ${ref.callId ?? '(room did not match the expected shape)'}`,
    `identity: ${ref.identity ?? '(unknown)'}`,
    `server:   ${ref.serverUrl ?? '(unknown)'}`,
  ].join('\n');
}
