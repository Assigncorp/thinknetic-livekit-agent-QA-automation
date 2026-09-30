import { RoomServiceClient } from 'livekit-server-sdk';

/**
 * The LiveKit server's view of the call the page is in.
 *
 * The browser can only show what the app renders. The server knows who is
 * really in the room, whether the caller's microphone track is REALLY muted at
 * the SFU (not just drawn as muted), and whether the agent left when the caller
 * did. Read-only: this never creates, edits or deletes anything.
 *
 * Needs LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in .env; tests that
 * use it skip without them rather than pass.
 */

export const AGENT_KIND = 4;
export const STANDARD_KIND = 0;
export const MICROPHONE_SOURCE = 2;

export function livekitServerAvailable(): string | null {
  const missing = ['LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET'].filter((n) => !process.env[n]);
  return missing.length ? `${missing.join(', ')} not set in .env` : null;
}

export interface ServerParticipant {
  identity: string;
  kind: number;
  attributes: Record<string, string>;
  tracks: { sid: string; source: number; muted: boolean; type: number }[];
}

export class LiveKitServer {
  private readonly client: RoomServiceClient;

  constructor() {
    const url = process.env.LIVEKIT_URL!.replace(/^wss:/, 'https:').replace(/^ws:/, 'http:');
    this.client = new RoomServiceClient(url, process.env.LIVEKIT_API_KEY!, process.env.LIVEKIT_API_SECRET!);
  }

  async participants(room: string): Promise<ServerParticipant[]> {
    try {
      const got = await this.client.listParticipants(room);
      return got.map((p) => ({
        identity: p.identity,
        kind: Number(p.kind),
        attributes: { ...(p.attributes ?? {}) },
        tracks: (p.tracks ?? []).map((t) => ({
          sid: t.sid,
          source: Number(t.source),
          muted: Boolean(t.muted),
          type: Number(t.type),
        })),
      }));
    } catch (err) {
      // A room that has closed is a 404 - which is an answer, not an error.
      if (/not.?found|does not exist/i.test(String(err))) return [];
      throw err;
    }
  }

  /** Polls until `predicate` holds; returns ms waited, or null on timeout. */
  async waitUntil(predicate: () => Promise<boolean>, timeoutMs: number, pollMs = 1000): Promise<number | null> {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
      if (await predicate()) return Date.now() - started;
      await new Promise((r) => setTimeout(r, pollMs));
    }
    return null;
  }
}
