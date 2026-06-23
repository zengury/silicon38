import { Router, Request, Response } from 'express';
import { getCache } from '../../cache/redis';
import { pool } from '../../db/pool';

const router = Router();

/**
 * GET /api/state
 *
 * Return the latest state for all robots (from Redis or DB fallback).
 */
router.get('/', async (_req: Request, res: Response) => {
  try {
    const cache = await getCache();
    const cached = await cache.getAllLatest();

    if (cached.length > 0) {
      return res.json({ data: cached, meta: { source: 'cache' } });
    }

    // Fallback to DB
    const result = await pool.query(
      `SELECT DISTINCT ON (robot_id)
         robot_id, battery_level, joint_temperatures, cpu_usage,
         network_latency, task, latitude, longitude, status, recorded_at as timestamp
       FROM telemetry
       ORDER BY robot_id, recorded_at DESC`,
    );

    return res.json({ data: formatRows(result.rows), meta: { source: 'db' } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * GET /api/state/:robotId
 *
 * Return the latest state for a single robot.
 */
router.get('/:robotId', async (req: Request, res: Response) => {
  try {
    const { robotId } = req.params;
    const cache = await getCache();
    const cached = await cache.getLatest(robotId);

    if (cached) {
      return res.json({ data: cached, meta: { source: 'cache' } });
    }

    const result = await pool.query(
      `SELECT robot_id, battery_level, joint_temperatures, cpu_usage,
              network_latency, task, latitude, longitude, status, recorded_at as timestamp
       FROM telemetry
       WHERE robot_id = $1
       ORDER BY recorded_at DESC
       LIMIT 1`,
      [robotId],
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: `Robot ${robotId} not found` },
      });
    }

    return res.json({ data: formatRow(result.rows[0]), meta: { source: 'db' } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

// ---------------------------------------------------------------------------
// Helpers
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

function formatRow(r: DbRow) {
  return {
    robot_id: r.robot_id,
    battery_level: r.battery_level,
    joint_temperatures: r.joint_temperatures || {},
    cpu_usage: r.cpu_usage,
    network_latency: r.network_latency,
    task: r.task,
    gps: { latitude: r.latitude, longitude: r.longitude },
    status: r.status,
    timestamp: r.timestamp,
  };
}

function formatRows(rows: DbRow[]) {
  return rows.map(formatRow);
}

export default router;
