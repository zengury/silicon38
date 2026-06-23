import { BaseAdapter } from './base-adapter';
import type { NormalizedTelemetry } from './types';

/**
 * STUB adapter for Modbus-protocol robots.
 *
 * Modbus is register-based, so the adapter maps numeric registers
 * to the unified schema. This stub implements enough to prove the
 * hot-plug property of the adapter registry.
 */
export class ModbusAdapter extends BaseAdapter {
  readonly protocol = 'modbus';

  normalize(raw: unknown): NormalizedTelemetry {
    if (raw === null || typeof raw !== 'object') {
      throw new Error('[modbus] Payload must be an object of register values');
    }

    const r = raw as Record<string, unknown>;

    this.requireFields(r, [
      'id',
      'bat',
      'temp',
      'cpu',
      'latency',
      'task',
      'lat',
      'lng',
      'status',
    ]);

    return {
      robot_id: String(r.id),
      battery_level: Number(r.bat),
      joint_temperatures: typeof r.temp === 'object'
        ? (r.temp as Record<string, number>)
        : { default: Number(r.temp) },
      cpu_usage: Number(r.cpu),
      network_latency: Number(r.latency),
      task: String(r.task),
      gps: {
        latitude: Number(r.lat),
        longitude: Number(r.lng),
      },
      status: this.mapStatus(Number(r.status)),
      timestamp: this.now(),
    };
  }

  private mapStatus(code: number): NormalizedTelemetry['status'] {
    // Modbus uses status register codes
    switch (code) {
      case 0: return 'offline';
      case 1: return 'online';
      case 2: return 'error';
      case 3: return 'maintenance';
      default: return 'error';
    }
  }
}
