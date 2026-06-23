import { WebSocketServer, WebSocket } from 'ws';
import type { Server } from 'http';
import { pool } from '../db/pool';
import { CollaborationManager } from '../collaboration/messages';
import { AlertEngine } from '../alert/engine';
import { configure as configureIngest } from './routes/data-ingest';

export interface WsContext {
  wss: WebSocketServer;
  collaboration: CollaborationManager;
  alertEngine: AlertEngine;
}

/**
 * Attach a WebSocket server to an HTTP server.
 *
 * The WebSocket serves three purposes:
 * 1. Real-time telemetry push (from ingest route via wss broadcast)
 * 2. Collaboration chat (handled by CollaborationManager)
 * 3. Alert notifications (pushed as part of telemetry_update)
 */
export function createWsServer(server: Server): WsContext {
  const wss = new WebSocketServer({ server, path: '/ws' });
  const collaboration = new CollaborationManager();
  const alertEngine = new AlertEngine();

  // Wire ingest route to use this WebSocket server and alert engine
  configureIngest({ alertEngine, wss });

  wss.on('connection', (ws: WebSocket, req) => {
    const url = new URL(req.url || '/', `http://${req.headers.host}`);
    const username = url.searchParams.get('user') || `user-${Date.now()}`;

    collaboration.connect(username, ws);

    ws.on('message', async (raw) => {
      try {
        const msg = JSON.parse(raw.toString());

        switch (msg.type) {
          case 'chat_message': {
            const { robot_id, content, mentions, handling } = msg.data || {};

            // Persist to DB
            if (content) {
              await pool.query(
                `INSERT INTO messages (robot_id, user_name, content, mentions, handling)
                 VALUES ($1,$2,$3,$4,$5)`,
                [robot_id || '', username, content, mentions || [], handling || false],
              );
            }

            // Broadcast
            collaboration.broadcast({
              robotId: robot_id || '',
              userName: username,
              content: content || '',
              mentions: mentions || [],
              handling: handling || false,
            });
            break;
          }

          case 'subscribe': {
            // Client subscribes to a robot's updates
            ws.send(JSON.stringify({
              type: 'subscribed',
              data: { robot_id: msg.data?.robot_id },
            }));
            break;
          }

          default:
            ws.send(JSON.stringify({
              type: 'error',
              data: { message: `Unknown message type: ${msg.type}` },
            }));
        }
      } catch (err: any) {
        ws.send(JSON.stringify({
          type: 'error',
          data: { message: err.message },
        }));
      }
    });

    ws.on('close', () => {
      collaboration.disconnect(username);
    });

    // Welcome message
    ws.send(JSON.stringify({
      type: 'connected',
      data: {
        user: username,
        onlineUsers: collaboration.getOnlineUsers(),
        adapters: [], // filled by frontend if needed
      },
    }));
  });

  console.log('[ws] WebSocket server ready on /ws');
  return { wss, collaboration, alertEngine };
}
