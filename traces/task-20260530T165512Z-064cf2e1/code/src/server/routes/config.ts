import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { pool } from '../../db/pool';
import { getCache } from '../../cache/redis';
import { reloadRules } from './data-ingest';

const router = Router();

const ConfigSetBody = z.object({
  key: z.string().min(1),
  value: z.unknown(),
});

// Allowed config keys
const ALLOWED_KEYS = new Set([
  'alert.default_battery_threshold',
  'alert.default_temp_threshold',
  'alert.default_cpu_threshold',
  'alert.default_latency_threshold',
  'sampling_frequency_s',
  'reconnect_policy.max_retries',
  'reconnect_policy.backoff_ms',
  'theme.default',
  'language.default',
]);

/**
 * GET /api/config
 *
 * Return all configuration values.
 */
router.get('/', async (_req: Request, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT key, value, updated_at FROM config ORDER BY key',
    );
    const config: Record<string, unknown> = {};
    for (const row of result.rows) {
      config[row.key] = row.value;
    }
    return res.json({ data: config });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * GET /api/config/:key
 *
 * Return a single configuration value.
 */
router.get('/:key', async (req: Request, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT value FROM config WHERE key = $1',
      [req.params.key],
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: `Config key '${req.params.key}' not found` },
      });
    }

    return res.json({ data: result.rows[0].value });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * PUT /api/config
 *
 * Set or update one or more configuration values.
 *
 * Body: { "key": "value", ... }
 */
router.put('/', async (req: Request, res: Response) => {
  if (typeof req.body !== 'object' || req.body === null) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: 'Body must be an object of key-value pairs' },
    });
  }

  const results: Record<string, unknown> = {};
  const errors: string[] = [];

  for (const [key, value] of Object.entries(req.body)) {
    if (!ALLOWED_KEYS.has(key)) {
      errors.push(`Key '${key}' is not allowed. Allowed: ${Array.from(ALLOWED_KEYS).join(', ')}`);
      continue;
    }

    try {
      await pool.query(
        `INSERT INTO config (key, value, updated_at)
         VALUES ($1, $2, now())
         ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = now()`,
        [key, JSON.stringify(value)],
      );
      results[key] = value;

      // Side effect: if alert threshold changed, reload alert rules
      if (key.startsWith('alert.')) {
        await reloadRules();
      }
    } catch (err: any) {
      errors.push(`Key '${key}': ${err.message}`);
    }
  }

  if (errors.length > 0 && Object.keys(results).length === 0) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: errors.join('; ') },
    });
  }

  return res.json({
    data: results,
    meta: { errors: errors.length > 0 ? errors : undefined },
  });
});

export default router;
