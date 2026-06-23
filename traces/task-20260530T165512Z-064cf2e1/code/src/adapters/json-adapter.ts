import { BaseAdapter } from './base-adapter';
import type { NormalizedTelemetry } from './types';

/**
 * Expected shape of incoming JSON telemetry.
 *
 * This is the FIRST protocol we support. The schema is deliberately
 * explicit so that anyone adding a new adapter later knows the contract.
 */
interface JsonTelemetryPayload {
  robotId: string;
  battery: number;
  joints: Record<string, number>;
  cpu: number;
  latency: number;
  task: string;
  latitude: number;
  longitude: number;
  status: string;
  ts?: string; // optional — adapter supplies current time if absent
}

/**
 * Adapter for robots that report via a JSON-based HTTP/WebSocket protocol.
 *
 * Normalizes the JSON payload into the unified {@link NormalizedTelemetry}
 * schema. Enforces all required fields via the base-class guard.
 */
export class JsonAdapter extends BaseAdapter {
  readonly protocol = 'json';

  normalize(raw: unknown): NormalizedTelemetry {
    if (raw === null || typeof raw !== 'object') {
      throw new Error('[json] Payload must be a JSON object');
    }

    const p = raw as Record<string, unknown>;

    this.requireFields(p, [
      'robotId',
      'battery',
      'joints',
      'cpu',
      'latency',
      'task',
      'latitude',
      'longitude',
      'status',
    ]);

    return {
      robot_id: String(p.robotId),
      battery_level: Number(p.battery),
      joint_temperatures: p.joints as Record<string, number>,
      cpu_usage: Number(p.cpu),
      network_latency: Number(p.latency),
      task: String(p.task),
      gps: {
        latitude: Number(p.latitude),
        longitude: Number(p.longitude),
      },
      status: this.mapStatus(String(p.status)),
      timestamp: typeof p.ts === 'string' ? p.ts : this.now(),
    };
  }

  /** Map arbitrary status strings to our constrained set. */
  private mapStatus(raw: string): NormalizedTelemetry['status'] {
    const s = raw.toLowerCase();
    if (s === 'online') return 'online';
    if (s === 'offline') return 'offline';
    if (s === 'error') return 'error';
    if (s === 'maintenance') return 'maintenance';
    // Unknown status → treat as 'error' (fail-safe)
    return 'error';
  }
}
