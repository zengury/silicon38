import { Router, Request, Response } from 'express';
import { healthCheck as dbHealth } from '../../db/pool';
import { getCache } from '../../cache/redis';

const router = Router();

router.get('/health', async (_req: Request, res: Response) => {
  const dbOk = await dbHealth();
  let cacheOk = false;
  try {
    const cache = await getCache();
    cacheOk = await cache.ping();
  } catch { /* ignore */ }

  const healthy = dbOk && cacheOk;

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'ok' : 'degraded',
    timestamp: new Date().toISOString(),
    db: dbOk ? 'up' : 'down',
    cache: cacheOk ? 'up' : 'down',
  });
});

export default router;
