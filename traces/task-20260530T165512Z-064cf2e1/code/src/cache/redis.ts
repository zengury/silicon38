import type { NormalizedTelemetry } from '../adapters/types';

/**
 * Type-safe Redis cache layer for the robot fleet monitor.
 *
 * In production this wraps the `redis` npm package.  For development
 * and testing the in-memory fallback is used when REDIS_URL is not set.
 */
export interface CacheStore {
  /** Store latest telemetry for a robot (overwrites previous). */
  setLatest(robotId: string, telemetry: NormalizedTelemetry): Promise<void>;

  /** Retrieve latest telemetry for a robot, or null. */
  getLatest(robotId: string): Promise<NormalizedTelemetry | null>;

  /** Retrieve latest telemetry for ALL robots. */
  getAllLatest(): Promise<NormalizedTelemetry[]>;

  /** Check health. */
  ping(): Promise<boolean>;
}

// ---------------------------------------------------------------------------
// In-Memory Fallback (used when REDIS_URL is not set)
// ---------------------------------------------------------------------------

class InMemoryCache implements CacheStore {
  private store = new Map<string, NormalizedTelemetry>();

  async setLatest(robotId: string, telemetry: NormalizedTelemetry): Promise<void> {
    this.store.set(robotId, telemetry);
  }

  async getLatest(robotId: string): Promise<NormalizedTelemetry | null> {
    return this.store.get(robotId) ?? null;
  }

  async getAllLatest(): Promise<NormalizedTelemetry[]> {
    return Array.from(this.store.values());
  }

  async ping(): Promise<boolean> {
    return true;
  }
}

// ---------------------------------------------------------------------------
// Redis-backed implementation
// ---------------------------------------------------------------------------

class RedisCache implements CacheStore {
  private client: any; // typed loosely to avoid hard redis dependency at import

  constructor() {
    // Lazy-load redis to avoid crashing when REDIS_URL is not set
    try {
      const { createClient } = require('redis');
      this.client = createClient({
        url: process.env.REDIS_URL || 'redis://localhost:6379',
      });
      this.client.on('error', (err: Error) => {
        console.error('[cache] Redis error:', err.message);
      });
    } catch {
      throw new Error('[cache] redis package not installed');
    }
  }

  async connect(): Promise<void> {
    await this.client.connect();
  }

  async setLatest(robotId: string, telemetry: NormalizedTelemetry): Promise<void> {
    await this.client.set(
      `robot:latest:${robotId}`,
      JSON.stringify(telemetry),
    );
  }

  async getLatest(robotId: string): Promise<NormalizedTelemetry | null> {
    const raw = await this.client.get(`robot:latest:${robotId}`);
    return raw ? JSON.parse(raw) : null;
  }

  async getAllLatest(): Promise<NormalizedTelemetry[]> {
    const keys = await this.client.keys('robot:latest:*');
    if (keys.length === 0) return [];
    const rawList = await this.client.mGet(keys);
    return rawList
      .filter((r: unknown) => r !== null)
      .map((r: string) => JSON.parse(r));
  }

  async ping(): Promise<boolean> {
    try {
      await this.client.ping();
      return true;
    } catch {
      return false;
    }
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

let cacheInstance: CacheStore | null = null;

export async function getCache(): Promise<CacheStore> {
  if (cacheInstance) return cacheInstance;

  if (process.env.REDIS_URL) {
    const redis = new RedisCache();
    await redis.connect();
    cacheInstance = redis;
  } else {
    console.log('[cache] No REDIS_URL set — using in-memory cache.');
    cacheInstance = new InMemoryCache();
  }

  return cacheInstance;
}
