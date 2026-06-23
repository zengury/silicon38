import { Router, Request, Response } from 'express';
import { z } from 'zod';
import { generatePdf, generateExcel } from '../../export/service';
import { getCache } from '../../cache/redis';
import type { NormalizedTelemetry } from '../../adapters/types';

const router = Router();

const ExportQuery = z.object({
  format: z.enum(['pdf', 'excel', 'csv']).default('pdf'),
  robot_id: z.string().optional(),
});

/**
 * GET /api/export
 *
 * Export current robot data as PDF, Excel, or CSV.
 * Query params:
 *   format — 'pdf' | 'excel' | 'csv'  (default: pdf)
 *   robot_id — optionally filter to a single robot
 */
router.get('/', async (req: Request, res: Response) => {
  try {
    const parsed = ExportQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({
        error: { code: 'VALIDATION_ERROR', message: parsed.error.message },
      });
    }

    const { format, robot_id } = parsed.data;

    // Collect data
    const cache = await getCache();
    let robots: NormalizedTelemetry[];

    if (robot_id) {
      const single = await cache.getLatest(robot_id);
      robots = single ? [single] : [];
    } else {
      robots = await cache.getAllLatest();
    }

    if (robots.length === 0) {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: 'No robot data available for export' },
      });
    }

    switch (format) {
      case 'pdf': {
        const pdf = await generatePdf(robots);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="robot-fleet-report.pdf"');
        return res.send(pdf);
      }

      case 'excel': {
        const excel = await generateExcel(robots);
        res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        res.setHeader('Content-Disposition', 'attachment; filename="robot-fleet-report.xlsx"');
        return res.send(excel);
      }

      case 'csv': {
        const csv = await generateExcel(robots);
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', 'attachment; filename="robot-fleet-report.csv"');
        return res.send(csv);
      }

      default:
        return res.status(400).json({
          error: { code: 'VALIDATION_ERROR', message: `Unsupported format: ${format}` },
        });
    }
  } catch (err: any) {
    return res.status(500).json({
      error: { code: 'INTERNAL_ERROR', message: err.message },
    });
  }
});

export default router;
