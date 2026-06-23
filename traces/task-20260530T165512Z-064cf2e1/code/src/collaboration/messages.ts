import type { WebSocket } from 'ws';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id?: number;
  robotId: string;
  userName: string;
  content: string;
  mentions: string[];
  handling: boolean;
  createdAt?: string;
}

// ---------------------------------------------------------------------------
// Collaboration Manager — manages WebSocket-based chat
// ---------------------------------------------------------------------------

export class CollaborationManager {
  /** Connected clients, keyed by some unique ID (e.g. username) */
  private clients = new Map<string, WebSocket>();

  /** Register a connected user. */
  connect(username: string, ws: WebSocket): void {
    this.clients.set(username, ws);
    this.broadcast({
      robotId: '',
      userName: 'system',
      content: `${username} joined`,
      mentions: [],
      handling: false,
    });
  }

  /** Remove a disconnected user. */
  disconnect(username: string): void {
    this.clients.delete(username);
    this.broadcast({
      robotId: '',
      userName: 'system',
      content: `${username} left`,
      mentions: [],
      handling: false,
    });
  }

  /** Get list of online users. */
  getOnlineUsers(): string[] {
    return Array.from(this.clients.keys());
  }

  /**
   * Broadcast a message to ALL connected clients.
   * Used for real-time push of collaboration and alert notifications.
   */
  broadcast(msg: ChatMessage): void {
    const payload = JSON.stringify({
      type: 'chat_message',
      data: msg,
    });

    for (const ws of this.clients.values()) {
      if (ws.readyState === ws.OPEN) {
        ws.send(payload);
      }
    }
  }

  /**
   * Send to specific usernames (for @mentions, targeted notifications).
   */
  sendToUsers(usernames: string[], msg: ChatMessage): void {
    const payload = JSON.stringify({
      type: 'chat_message',
      data: msg,
    });

    for (const username of usernames) {
      const ws = this.clients.get(username);
      if (ws && ws.readyState === ws.OPEN) {
        ws.send(payload);
      }
    }
  }
}
