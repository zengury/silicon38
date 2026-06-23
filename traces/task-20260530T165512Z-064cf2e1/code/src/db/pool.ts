import { Pool, PoolConfig } from 'pg';
import * as fs from 'fs';
import * as path from 'path';

const poolConfig: PoolConfig = {
  host: process.env.PGHOST || 'localhost',
  port: Number(process.env.PGPORT) || 5432,
  database: process.env.PGDATABASE || 'robot_fleet',
  user: process.env.PGUSER || 'postgres',
  password: process.env.PGPASSWORD || 'postgres',
  max: 20,                      // pool size
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
};

export const pool = new Pool(poolConfig);

pool.on('error', (err) => {
  console.error('[db] Unexpected pool error:', err.message);
});

/** Run schema migration from schema.sql. Idempotent for CREATE IF NOT EXISTS. */
export async function migrate(): Promise<void> {
  const sqlPath = path.resolve(__dirname, 'schema.sql');
  const sql = fs.readFileSync(sqlPath, 'utf-8');
  await pool.query(sql);
  console.log('[db] Schema migration complete.');
}

/** Simple health check — returns true if DB is reachable. */
export async function healthCheck(): Promise<boolean> {
  try {
    await pool.query('SELECT 1');
    return true;
  } catch {
    return false;
  }
}
