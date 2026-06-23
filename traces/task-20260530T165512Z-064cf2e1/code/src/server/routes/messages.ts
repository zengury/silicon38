import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { pool } from '../../db/pool';

const router = Router();

const SendMessageBody = z.object({
  robot_id: z.string().min(1),
  user_name: z.string().min(1),
  content: z.string().min(1),
  mentions: z.array(z.string()).default([]),
  handling: z.boolean().default(false),
});

/**
 * GET /api/messages
 *
 * Return recent messages, optionally filtered by robot.
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 100, 500);
    const robotId = req.query.robot_id as string | undefined;

    let query = 'SELECT id, robot_id, user_name, content, mentions, handling, created_at FROM messages';
    const params: any[] = [];

    if (robotId) {
      query += ' WHERE robot_id = $1';
      params.push(robotId);
    }

    query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1);
    params.push(limit);

    const result = await pool.query(query, params);
    return res.json({ data: result.rows, meta: { count: result.rows.length } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * POST /api/messages
 *
 * Persist a new message and return it. The CollaborationManager
 * handles real-time broadcasting via WebSocket (not this REST route).
 */
router.post('/', async (req: Request, res: Response) => {
  const parsed = SendMessageBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
    });
  }

  const { robot_id, user_name, content, mentions, handling } = parsed.data;

  try {
    const result = await pool.query(
      `INSERT INTO messages (robot_id, user_name, content, mentions, handling)
       VALUES ($1,$2,$3,$4,$5) RETURNING *`,
      [robot_id, user_name, content, mentions, handling],
    );

    return res.status(201).json({ data: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

export default router;
