import { BaseAdapter } from './base-adapter';
import type { NormalizedTelemetry } from './types';

/**
 * STUB adapter for Protobuf-encoded robot telemetry.
 *
 * Protobuf support is NOT required in the initial release, but the
 * architecture must prove that adding a new protocol is a single-file
 * change. This stub implements a realistic `normalize()` path and
 * validates the registry's hot-plug capability.
 */
export class ProtobufAdapter extends BaseAdapter {
  readonly protocol = 'protobuf';

  normalize(raw: unknown): NormalizedTelemetry {
    // In production this would decode a protobuf-serialized buffer.
    // For now we accept a plain object matching the protobuf shape.
    if (raw === null || typeof raw !== 'object') {
      throw new Error('[protobuf] Payload must be a decoded protobuf object');
    }

    const p = raw as Record<string, unknown>;

    this.requireFields(p, [
      'robot_id',
      'battery_pct',
      'joint_temp_c',
      'cpu_pct',
      'latency_ms',
      'task_name',
      'lat',
      'lng',
      'status',
    ]);

    return {
      robot_id: String(p.robot_id),
      battery_level: Number(p.battery_pct),
      joint_temperatures: p.joint_temp_c as Record<string, number>,
      cpu_usage: Number(p.cpu_pct),
      network_latency: Number(p.latency_ms),
      task: String(p.task_name),
      gps: {
        latitude: Number(p.lat),
        longitude: Number(p.lng),
      },
      status: this.toStatus(String(p.status)),
      timestamp: this.now(),
    };
  }

  private toStatus(raw: string): NormalizedTelemetry['status'] {
    const s = raw.toLowerCase();
    if (s === 'online') return 'online';
    if (s === 'offline') return 'offline';
    if (s === 'error') return 'error';
    if (s === 'maintenance') return 'maintenance';
    return 'error';
  }
}
