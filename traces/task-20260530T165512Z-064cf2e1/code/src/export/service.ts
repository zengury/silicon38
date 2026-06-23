import type { NormalizedTelemetry } from '../adapters/types';

/**
 * Export service — generates PDF and Excel reports.
 *
 * PDF: Uses Puppeteer to render a headless browser view (matches screen).
 * Excel: Uses exceljs to produce spreadsheet data.
 *
 * In a real deployment these would render actual dashboard views.
 * For the initial implementation they produce structured data reports.
 */

export async function generatePdf(
  robots: NormalizedTelemetry[],
): Promise<Buffer> {
  // In production this would launch Puppeteer and render the dashboard.
  // For now produce a basic HTML→PDF content.
  const html = buildReportHtml(robots);
  
  let puppeteer: any;
  try {
    puppeteer = require('puppeteer');
  } catch {
    // Fallback: return HTML as "PDF" for environments without Chrome
    return Buffer.from(
      `<html><body><h1>Robot Fleet Report</h1>${html}</body></html>`,
      'utf-8',
    );
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();
    await page.setContent(
      `<html><body style="font-family: sans-serif;">${html}</body></html>`,
    );
    const pdf = await page.pdf({ format: 'A4', printBackground: true });
    return Buffer.from(pdf);
  } finally {
    await browser.close();
  }
}

export async function generateExcel(
  robots: NormalizedTelemetry[],
  history?: NormalizedTelemetry[],
): Promise<Buffer> {
  let ExcelJS: any;
  try {
    ExcelJS = require('exceljs');
  } catch {
    // Fallback: produce CSV
    return buildCsv(robots, history);
  }

  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'Robot Fleet Monitor';

  // Sheet 1: Latest State
  const stateSheet = workbook.addWorksheet('Latest State');
  stateSheet.columns = [
    { header: 'Robot ID', key: 'robot_id', width: 15 },
    { header: 'Battery %', key: 'battery_level', width: 12 },
    { header: 'CPU %', key: 'cpu_usage', width: 10 },
    { header: 'Latency ms', key: 'network_latency', width: 12 },
    { header: 'Status', key: 'status', width: 12 },
    { header: 'Task', key: 'task', width: 20 },
    { header: 'Latitude', key: 'latitude', width: 12 },
    { header: 'Longitude', key: 'longitude', width: 12 },
    { header: 'Timestamp', key: 'timestamp', width: 25 },
  ];

  for (const r of robots) {
    stateSheet.addRow({
      robot_id: r.robot_id,
      battery_level: r.battery_level,
      cpu_usage: r.cpu_usage,
      network_latency: r.network_latency,
      status: r.status,
      task: r.task,
      latitude: r.gps.latitude,
      longitude: r.gps.longitude,
      timestamp: r.timestamp,
    });
  }

  // Sheet 2: History (if provided)
  if (history && history.length > 0) {
    const historySheet = workbook.addWorksheet('History');
    historySheet.columns = stateSheet.columns;
    for (const r of history) {
      historySheet.addRow({
        robot_id: r.robot_id,
        battery_level: r.battery_level,
        cpu_usage: r.cpu_usage,
        network_latency: r.network_latency,
        status: r.status,
        task: r.task,
        latitude: r.gps.latitude,
        longitude: r.gps.longitude,
        timestamp: r.timestamp,
      });
    }
  }

  const buffer = await workbook.xlsx.writeBuffer();
  return Buffer.from(buffer);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildReportHtml(robots: NormalizedTelemetry[]): string {
  const rows = robots
    .map(
      (r) =>
        `<tr>
          <td>${r.robot_id}</td>
          <td>${r.battery_level.toFixed(1)}%</td>
          <td>${r.cpu_usage.toFixed(1)}%</td>
          <td>${r.network_latency}ms</td>
          <td>${r.status}</td>
          <td>${r.task}</td>
        </tr>`,
    )
    .join('');

  return `
    <h1>Robot Fleet Report</h1>
    <p>Generated: ${new Date().toISOString()}</p>
    <table border="1" cellpadding="6" cellspacing="0">
      <thead>
        <tr>
          <th>Robot ID</th><th>Battery</th><th>CPU</th>
          <th>Latency</th><th>Status</th><th>Task</th>
        </tr>
      </thead>
      <tbody>${rows || '<tr><td colspan="6">No data</td></tr>'}</tbody>
    </table>
  `;
}

function buildCsv(
  robots: NormalizedTelemetry[],
  history?: NormalizedTelemetry[],
): Buffer {
  const headers = 'robot_id,battery_level,cpu_usage,network_latency,status,task,latitude,longitude,timestamp\n';
  const rows = (history ?? robots)
    .map(
      (r) =>
        `${r.robot_id},${r.battery_level},${r.cpu_usage},${r.network_latency},${r.status},${r.task},${r.gps.latitude},${r.gps.longitude},${r.timestamp}`,
    )
    .join('\n');
  return Buffer.from(headers + rows, 'utf-8');
}
