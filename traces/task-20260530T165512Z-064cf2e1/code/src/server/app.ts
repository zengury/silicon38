import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import healthRouter from './routes/health';
import ingestRouter from './routes/data-ingest';
import stateRouter from './routes/state';
import historyRouter from './routes/history';
import alertsRouter from './routes/alerts';
import configRouter from './routes/config';
import messagesRouter from './routes/messages';
import exportRouter from './routes/export';

export function createApp(): express.Express {
  const app = express();

  // Middleware
  app.use(helmet({
    contentSecurityPolicy: false, // allow chart rendering
  }));
  app.use(cors());
  app.use(express.json({ limit: '1mb' }));

  // Routes
  app.use('/api', healthRouter);
  app.use('/api', ingestRouter);
  app.use('/api/state', stateRouter);
  app.use('/api/history', historyRouter);
  app.use('/api/alerts', alertsRouter);
  app.use('/api/config', configRouter);
  app.use('/api/messages', messagesRouter);
  app.use('/api/export', exportRouter);

  // 404
  app.use((_req, res) => {
    res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'The requested resource was not found' },
    });
  });

  // Global error handler
  app.use((
    err: Error,
    _req: express.Request,
    res: express.Response,
    _next: express.NextFunction,
  ) => {
    console.error('[app] Unhandled error:', err);
    res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
    });
  });

  return app;
}
