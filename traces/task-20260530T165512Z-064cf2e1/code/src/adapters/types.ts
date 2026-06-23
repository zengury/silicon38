/**
 * Unified Internal Schema for Robot Telemetry Data.
 *
 * Every adapter MUST normalize incoming data into this schema.
 * Fields that the source protocol does not provide are left undefined.
 */
export interface NormalizedTelemetry {
  /** Unique robot identifier, assigned by the fleet system */
  robot_id: string;

  /** Battery level as a percentage (0.0–100.0) */
  battery_level: number;

  /** Joint temperatures in degrees Celsius, keyed by joint name */
  joint_temperatures: Record<string, number>;

  /** CPU usage as a percentage (0.0–100.0) */
  cpu_usage: number;

  /** Network latency in milliseconds */
  network_latency: number;

  /** Current task description or task ID */
  task: string;

  /** GPS coordinates */
  gps: { latitude: number; longitude: number };

  /** Machine-readable status: online | offline | error | maintenance */
  status: 'online' | 'offline' | 'error' | 'maintenance';

  /** Timestamp of the data sample (ISO-8601) */
  timestamp: string;
}

/**
 * Type-safe robot status constants.
 */
export const ROBOT_STATUSES = ['online', 'offline', 'error', 'maintenance'] as const;
export type RobotStatus = (typeof ROBOT_STATUSES)[number];

/**
 * Robot metadata stored outside telemetry — stable properties that
 * describe the robot rather than a single telemetry sample.
 */
export interface RobotMeta {
  robot_id: string;
  name: string;
  protocol: string;
  registered_at: string;
}
