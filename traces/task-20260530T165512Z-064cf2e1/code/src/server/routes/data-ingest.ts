import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { registry } from '../../adapters';
import { pool } from '../../db/pool';
import { getCache } from '../../cache/redis';
import { AlertEngine } from '../../alert/engine';
import type { AlertRule } from '../../alert/engine';
import type { WebSocketServer } from 'ws';
import type { NormalizedTelemetry } from '../../adapters/types';

// ---------------------------------------------------------------------------
// Validation schemas
// ---------------------------------------------------------------------------

const IngestBody = z.object({
  protocol: z.string().min(1),
  robot_id: z.string().min(1).optional(),
  data: z.unknown(), // raw payload — adapter validates structure
});

const RegisterRobotBody = z.object({
  robot_id: z.string().min(1),
  name: z.string().min(1),
  protocol: z.string().min(1),
});

// ---------------------------------------------------------------------------
// Shared references (set by the app on startup)
// ---------------------------------------------------------------------------

let alertEngine: AlertEngine | null = null;
let wss: WebSocketServer | null = null;
let cachedRules: AlertRule[] = [];

/**
 * Call once during app startup so the ingest route can trigger alerts
 * and push real-time updates to WebSocket clients.
 */
export function configure(options: {
  alertEngine: AlertEngine;
  wss: WebSocketServer;
}): void {
  alertEngine = options.alertEngine;
  wss = options.wss;
}

/**
 * Reload alert rules from the database. Called after config changes.
 */
async function reloadRules(): Promise<void> {
  try {
    const result = await pool.query(
      'SELECT id, name, metric, operator, threshold, target_value, severity, enabled, cooldown_s, escalate_after_s FROM alert_rules WHERE enabled = true',
    );
    cachedRules = result.rows.map((r: any) => ({
      id: r.id,
      name: r.name,
      metric: r.metric,
      operator: r.operator,
      threshold: r.threshold,
      targetValue: r.target_value,
      severity: r.severity,
      enabled: r.enabled,
      cooldownS: r.cooldown_s,
      escalateAfterS: r.escalate_after_s,
    }));
  } catch (err) {
    console.error('[ingest] Failed to load alert rules:', err);
  }
}

// Load rules once at module init (best-effort).
reloadRules();

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

const router = Router();

/**
 * POST /api/ingest
 *
 * Receive raw robot data, normalize it via the adapter registry,
 * store in PostgreSQL + Redis, run alert evaluation, and push via WebSocket.
 */
router.post('/ingest', async (req: Request, res: Response) => {
  try {
    const parsed = IngestBody.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
      });
    }

    const { protocol, data } = parsed.data;

    // 1. Normalize via adapter
    let normalized: NormalizedTelemetry;
    try {
      normalized = registry.normalize(protocol, data);
    } catch (normErr: any) {
      return res.status(400).json({
        error: {
          code: 'NORMALIZATION_ERROR',
          message: normErr.message,
        },
      });
    }

    // 2. Store in PostgreSQL
    await pool.query(
      `INSERT INTO telemetry (robot_id, battery_level, joint_temperatures, cpu_usage, network_latency, task, latitude, longitude, status, recorded_at)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
       ON CONFLICT (robot_id, recorded_at) DO NOTHING`,
      [
        normalized.robot_id,
        normalized.battery_level,
        JSON.stringify(normalized.joint_temperatures),
        normalized.cpu_usage,
        normalized.network_latency,
        normalized.task,
        normalized.gps.latitude,
        normalized.gps.longitude,
        normalized.status,
        normalized.timestamp,
      ],
    );

    // 3. Update Redis cache
    const cache = await getCache();
    await cache.setLatest(normalized.robot_id, normalized);

    // 4. Evaluate alerts
    const firedAlerts = alertEngine
      ? alertEngine.evaluateAll(cachedRules, normalized)
      : [];

    for (const alert of firedAlerts) {
      await pool.query(
        `INSERT INTO alerts (rule_id, robot_id, metric, value, severity, message, fired_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7)`,
        [
          alert.ruleId,
          alert.robotId,
          alert.metric,
          alert.value,
          alert.severity,
          alert.message,
          alert.firedAt,
        ],
      );
    }

    // 5. Push via WebSocket
    if (wss) {
      const pushPayload = JSON.stringify({
        type: 'telemetry_update',
        data: normalized,
        alerts: firedAlerts,
      });
      for (const client of wss.clients) {
        if (client.readyState === client.OPEN) {
          client.send(pushPayload);
        }
      }
    }

    return res.status(201).json({
      data: normalized,
      meta: { alerts_fired: firedAlerts.length },
    });
  } catch (err: any) {
    console.error('[ingest] Unexpected error:', err);
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * POST /api/robots/register
 *
 * Register a new robot in the system so its telemetry can be accepted.
 */
router.post('/robots/register', async (req: Request, res: Response) => {
  const parsed = RegisterRobotBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
    });
  }

  const { robot_id, name, protocol: proto } = parsed.data;

  // Verify adapter exists for protocol
  if (!registry.listProtocols().includes(proto.toLowerCase())) {
    return res.status(400).json({
      error: {
        code: 'UNSUPPORTED_PROTOCOL',
        message: `No adapter registered for protocol: ${proto}. Available: ${registry.listProtocols().join(', ')}`,
      },
    });
  }

  try {
    await pool.query(
      'INSERT INTO robots (robot_id, name, protocol) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING',
      [robot_id, name, proto.toLowerCase()],
    );
    return res.status(201).json({ data: { robot_id, name, protocol: proto } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/** GET /api/ingest/rules — reload alert rules (called by config changes) */
router.get('/rules/reload', async (_req: Request, res: Response) => {
  await reloadRules();
  res.json({ data: { count: cachedRules.length } });
});

export { reloadRules };
export default router;
