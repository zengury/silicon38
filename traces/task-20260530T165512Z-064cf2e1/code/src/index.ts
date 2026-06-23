import http from 'http';
import { createApp } from './server/app';
import { createWsServer } from './server/ws-server';
import { migrate } from './db/pool';
import { registry, JsonAdapter, ProtobufAdapter, ModbusAdapter } from './adapters';

/**
 * Robot Fleet Monitor — Main Entrypoint
 *
 * Starts:
 *  1. Database migration
 *  2. Adapter registration
 *  3. Express HTTP server
 *  4. WebSocket server
 */
async function main() {
  // 1. Register adapters (hot-plug: add new adapters here)
  registry.register(new JsonAdapter());
  registry.register(new ProtobufAdapter());
  registry.register(new ModbusAdapter());
  console.log(`[boot] Registered adapters: ${registry.listProtocols().join(', ')}`);

  // 2. Run DB migrations
  try {
    await migrate();
    console.log('[boot] Database migrations complete');
  } catch (err: any) {
    console.warn('[boot] Database migration failed (non-fatal for dev):', err.message);
  }

  // 3. Create Express app
  const app = createApp();

  // 4. Create HTTP server
  const server = http.createServer(app);

  // 5. Attach WebSocket
  const wsCtx = createWsServer(server);

  // 6. Start listening
  const PORT = Number(process.env.PORT) || 3000;
  const HOST = process.env.HOST || '0.0.0.0';

  server.listen(PORT, HOST, () => {
    console.log(`[boot] Robot Fleet Monitor running on http://${HOST}:${PORT}`);
    console.log(`[boot] WebSocket on ws://${HOST}:${PORT}/ws`);
    console.log(`[boot] Health: http://${HOST}:${PORT}/api/health`);
  });

  // Graceful shutdown
  const shutdown = async () => {
    console.log('[boot] Shutting down...');
    server.close();
    process.exit(0);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

main().catch((err) => {
  console.error('[boot] Fatal error:', err);
  process.exit(1);
});
