import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { pool } from '../../db/pool';
import { reloadRules } from './data-ingest';

const router = Router();

const AlertRuleBody = z.object({
  name: z.string().min(1),
  metric: z.string().min(1),
  operator: z.enum(['<', '>', '==', '!=', '<=', '>=']),
  threshold: z.number().nullable().optional(),
  target_value: z.string().nullable().optional(),
  severity: z.enum(['info', 'warning', 'critical']).default('warning'),
  enabled: z.boolean().default(true),
  cooldown_s: z.number().int().min(0).default(300),
  escalate_after_s: z.number().int().nullable().optional(),
});

const AlertRuleUpdateBody = AlertRuleBody.partial();

/**
 * GET /api/alerts/rules — list all alert rules.
 */
router.get('/rules', async (_req: Request, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT id, name, metric, operator, threshold, target_value, severity,
              enabled, cooldown_s, escalate_after_s, created_at, updated_at
       FROM alert_rules ORDER BY id`,
    );
    return res.json({ data: result.rows });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * POST /api/alerts/rules — create a new alert rule.
 */
router.post('/rules', async (req: Request, res: Response) => {
  const parsed = AlertRuleBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
    });
  }

  const r = parsed.data;

  try {
    const result = await pool.query(
      `INSERT INTO alert_rules (name, metric, operator, threshold, target_value, severity, enabled, cooldown_s, escalate_after_s)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING *`,
      [r.name, r.metric, r.operator, r.threshold ?? null, r.target_value ?? null,
       r.severity, r.enabled, r.cooldown_s, r.escalate_after_s ?? null],
    );
    await reloadRules();
    return res.status(201).json({ data: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * PATCH /api/alerts/rules/:id — update an existing rule.
 */
router.patch('/rules/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const parsed = AlertRuleUpdateBody.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
    });
  }

  const fields = parsed.data;
  const sets: string[] = [];
  const values: any[] = [];
  let i = 1;

  for (const [key, val] of Object.entries(fields)) {
    if (val !== undefined) {
      const col = key === 'target_value' ? 'target_value' :
                  key === 'cooldown_s' ? 'cooldown_s' :
                  key === 'escalate_after_s' ? 'escalate_after_s' : key;
      sets.push(`${col} = $${i}`);
      values.push(val);
      i++;
    }
  }

  if (sets.length === 0) {
    return res.json({ data: null, meta: { message: 'No fields to update' } });
  }

  sets.push(`updated_at = now()`);

  try {
    const result = await pool.query(
      `UPDATE alert_rules SET ${sets.join(', ')} WHERE id = $${i} RETURNING *`,
      [...values, Number(id)],
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: `Rule ${id} not found` },
      });
    }

    await reloadRules();
    return res.json({ data: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * DELETE /api/alerts/rules/:id — remove an alert rule.
 */
router.delete('/rules/:id', async (req: Request, res: Response) => {
  try {
    const result = await pool.query(
      'DELETE FROM alert_rules WHERE id = $1 RETURNING id',
      [Number(req.params.id)],
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: `Rule ${req.params.id} not found` },
      });
    }

    await reloadRules();
    return res.json({ data: { deleted: result.rows[0].id } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

/**
 * GET /api/alerts — recent alerts history.
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const limit = Math.min(Number(req.query.limit) || 100, 500);

    const result = await pool.query(
      `SELECT a.id, a.rule_id, a.robot_id, a.metric, a.value, a.severity,
              a.message, a.acknowledged, a.fired_at, a.resolved_at,
              ar.name as rule_name
       FROM alerts a
       LEFT JOIN alert_rules ar ON a.rule_id = ar.id
       ORDER BY a.fired_at DESC
       LIMIT $1`,
      [limit],
    );

    return res.json({ data: result.rows, meta: { count: result.rows.length } });
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

export default router;
