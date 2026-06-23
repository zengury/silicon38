/* ============================================
 * API Contract Types — mirrors api-designer-contract-v1
 * ============================================ */

export type RobotStatus = 'online' | 'offline' | 'error' | 'warning' | 'idle' | 'charging';

export interface BatteryStatus {
  levelPercent: number;
  voltage: number;
  isCharging: boolean;
}

export interface JointStatus {
  jointId: string;
  temperatureCelsius: number;
  isConnected: boolean;
  angleDegrees: number;
}

export interface CpuStatus {
  usagePercent: number;
  temperatureCelsius: number;
}

export interface NetworkStatus {
  latencyMs: number;
  signalStrength: number;
  isConnected: boolean;
}

export interface TaskStatus {
  taskId: string;
  name: string;
  state: 'queued' | 'in_progress' | 'completed' | 'failed';
  progressPercent: number;
  startedAt: string | null;
  estimatedCompletionAt: string | null;
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  altitudeMeters: number;
}

export interface RobotTelemetry {
  robotId: string;
  timestamp: string;
  battery: BatteryStatus;
  joints: JointStatus[];
  cpu: CpuStatus;
  network: NetworkStatus;
  task: TaskStatus | null;
  location: GeoLocation;
  metadata: Record<string, unknown>;
}

export interface RobotSummary {
  robotId: string;
  name: string;
  model: string;
  status: RobotStatus;
  batteryLevelPercent: number;
  currentTask: string | null;
  lastSeenAt: string;
}

export interface RobotDetail {
  robotId: string;
  name: string;
  model: string;
  firmwareVersion: string;
  status: RobotStatus;
  lastTelemetry: RobotTelemetry | null;
  config: RobotConfig;
  createdAt: string;
  updatedAt: string;
}

export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

export interface Alert {
  alertId: string;
  robotId: string;
  ruleId: string;
  severity: AlertSeverity;
  message: string;
  details: Record<string, unknown>;
  triggeredAt: string;
  acknowledgedAt: string | null;
  acknowledgedBy: string | null;
  resolvedAt: string | null;
}

export interface AlertThresholds {
  batteryLowPercent: number;
  jointTemperatureHighCelsius: number;
  cpuTemperatureHighCelsius: number;
  networkLatencyHighMs: number;
  tiltAngleDegrees: number;
}

export interface ReconnectStrategy {
  maxRetries: number;
  baseDelayMs: number;
  backoffMultiplier: number;
}

export interface RobotConfig {
  robotId: string;
  alertThresholds: AlertThresholds;
  samplingIntervalMs: number;
  reconnectStrategy: ReconnectStrategy;
}

export interface Comment {
  commentId: string;
  robotId: string;
  authorId: string;
  authorName: string;
  content: string;
  mentions: string[];
  createdAt: string;
  updatedAt: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: { field?: string; message: string; code?: string }[];
  };
  meta: { requestId: string };
}

/* ========== WebSocket Event Types ========== */
export type WsEventType =
  | 'telemetry_update'
  | 'alert'
  | 'robot_status_change'
  | 'comment'
  | 'mention';

export interface WsMessage {
  type: WsEventType;
  [key: string]: unknown;
}

export interface WsTelemetryUpdate extends WsMessage {
  type: 'telemetry_update';
  robotId: string;
  telemetry: RobotTelemetry;
}

export interface WsAlertEvent extends WsMessage {
  type: 'alert';
  alert: Alert;
}

export interface WsRobotStatusChange extends WsMessage {
  type: 'robot_status_change';
  robotId: string;
  status: RobotStatus;
}

export interface WsCommentEvent extends WsMessage {
  type: 'comment';
  comment: Comment;
}

/* ========== Dashboard Layout ========== */
export type ViewMode = 'overview' | 'detail' | 'timeline';
export type ThemeMode = 'light' | 'dark';
export type Language = 'zh-CN' | 'en';

export interface DashboardLayout {
  viewMode: ViewMode;
  selectedRobotId: string | null;
  isFleetOverviewExpanded: boolean;
  isTimelineOpen: boolean;
}

/* ========== Simulated Data Types (Demo) ========== */
export interface SimulatedRobot {
  robotId: string;
  name: string;
  model: string;
  status: RobotStatus;
  battery: BatteryStatus;
  joints: JointStatus[];
  cpu: CpuStatus;
  network: NetworkStatus;
  task: TaskStatus | null;
  location: GeoLocation;
  lastSeenAt: string;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}
