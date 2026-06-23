import { Router, Request, Response } from 'express';
import { pool } from '../../db/pool';
import { z } from 'zod';

const router = Router();

const HistoryQuery = z.object({
  days: z.coerce.number().int().min(1).max(30).optional().default(30),
  limit: z.coerce.number().int().min(1).max(10000).optional().default(1000),
});

/**
 * GET /api/history/:robotId
 *
 * Return historical telemetry for a single robot.
 * Query params:
 *   days  — number of days to look back (default 30, max 30)
 *   limit — max rows (default 1000)
 */
router.get('/:robotId', async (req: Request, res: Response) => {
  try {
    const { robotId } = req.params;
    const parsed = HistoryQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
      });
    }

    const { days, limit } = parsed.data;

    const result = await pool.query(
      `SELECT robot_id, battery_level, joint_temperatures, cpu_usage,
              network_latency, task, latitude, longitude, status, recorded_at as timestamp
       FROM telemetry
       WHERE robot_id = $1 AND recorded_at > now() - ($2 || ' days')::INTERVAL
       ORDER BY recorded_at DESC
       LIMIT $3`,
      [robotId, String(days), limit],
    );

    return res.json({ data: formatRows(result.rows), meta: { days, count: result.rows.length } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * GET /api/history
 *
 * Return recent telemetry across ALL robots (for summary dashboards).
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const parsed = HistoryQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
      });
    }

    const { days, limit } = parsed.data;

    const result = await pool.query(
      `SELECT robot_id, battery_level, joint_temperatures, cpu_usage,
              network_latency, task, latitude, longitude, status, recorded_at as timestamp
       FROM telemetry
       WHERE recorded_at > now() - ($1 || ' days')::INTERVAL
       ORDER BY recorded_at DESC
       LIMIT $2`,
      [String(days), limit],
    );

    return res.json({ data: formatRows(result.rows), meta: { days, count: result.rows.length } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

// ---------------------------------------------------------------------------

interface DbRow {
  robot_id: string;
  battery_level: number;
  joint_temperatures: any;
  cpu_usage: number;
  network_latency: number;
  task: string;
  latitude: number;
  longitude: number;
  status: string;
  timestamp: string;
}

function formatRows(rows: DbRow[]) {
  return rows.map((r) => ({
    robot_id: r.robot_id,
    battery_level: r.battery_level,
    joint_temperatures: r.joint_temperatures || {},
    cpu_usage: r.cpu_usage,
    network_latency: r.network_latency,
    task: r.task,
    gps: { latitude: r.latitude, longitude: r.longitude },
    status: r.status,
    timestamp: r.timestamp,
  }));
}

export default router;
