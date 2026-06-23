import { pool } from './pool';

/**
 * Standalone migration runner: `ts-node src/db/migrate.ts`
 */
async function main() {
  const { migrate } = await import('./pool');
  await migrate();
  await pool.end();
  console.log('[db] Migration done.');
}

main().catch((err) => {
  console.error('[db] Migration failed:', err);
  process.exit(1);
});
