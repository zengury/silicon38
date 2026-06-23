// Robot Fleet Monitoring Dashboard - API Contracts
// Language: TypeScript (Node.js + Express)
// All interfaces are caller-oriented, with explicit optional/nullable fields.

// ============================================================
// 1. Data Ingestion & Normalization
// ============================================================

// Unified normalized robot telemetry schema
// All adapters must produce this shape.
export interface RobotTelemetry {
  robotId: string;          // Unique robot identifier
  timestamp: string;        // ISO 8601 UTC
  battery: BatteryStatus;
  joints: JointStatus[];
  cpu: CpuStatus;
  network: NetworkStatus;
  task: TaskStatus | null;  // null if idle
  location: GeoLocation;
  metadata: Record<string, unknown>; // Extensible for robot-specific fields
}

export interface BatteryStatus {
  levelPercent: number;     // 0-100
  voltage: number;          // Volts
  isCharging: boolean;
}

export interface JointStatus {
  jointId: string;          // e.g., "arm_left_shoulder"
  temperatureCelsius: number;
  isConnected: boolean;
  angleDegrees: number;     // -180 to 180
}

export interface CpuStatus {
  usagePercent: number;     // 0-100
  temperatureCelsius: number;
}

export interface NetworkStatus {
  latencyMs: number;
  signalStrength: number;   // 0-100 (RSSI scaled)
  isConnected: boolean;
}

export interface TaskStatus {
  taskId: string;
  name: string;
  state: 'queued' | 'in_progress' | 'completed' | 'failed';
  progressPercent: number;  // 0-100
  startedAt: string | null; // ISO 8601
  estimatedCompletionAt: string | null;
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  altitudeMeters: number;
}

// ============================================================
// 2. REST API Endpoints
// ============================================================

// --- Robots ---

// GET /api/v1/robots
// Query parameters
interface GetRobotsQuery {
  status?: 'online' | 'offline' | 'error';
  page?: number;            // default 1
  limit?: number;           // default 20, max 100
}

interface GetRobotsResponse {
  data: RobotSummary[];
  meta: PaginationMeta;
}

interface RobotSummary {
  robotId: string;
  name: string;
  model: string;
  status: 'online' | 'offline' | 'error';
  batteryLevelPercent: number;
  currentTask: string | null;
  lastSeenAt: string;       // ISO 8601
}

interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

// GET /api/v1/robots/:robotId
interface GetRobotResponse {
  data: RobotDetail;
}

interface RobotDetail {
  robotId: string;
  name: string;
  model: string;
  firmwareVersion: string;
  status: 'online' | 'offline' | 'error';
  lastTelemetry: RobotTelemetry | null;
  config: RobotConfig;
  createdAt: string;
  updatedAt: string;
}

// --- Telemetry ---

// POST /api/v1/robots/:robotId/telemetry (used by adapters)
interface PostTelemetryRequest {
  // Raw data in robot-specific format; adapter normalizes server-side
  raw: unknown;
  protocol: 'json' | 'protobuf' | 'modbus';
}

interface PostTelemetryResponse {
  data: {
    accepted: boolean;
    normalized: RobotTelemetry;
  };
}

// GET /api/v1/robots/:robotId/telemetry?from=&to=&interval=
interface GetTelemetryQuery {
  from: string;             // ISO 8601, inclusive
  to: string;               // ISO 8601, exclusive
  interval?: string;        // Aggregation interval, e.g., "1m", "5m", "1h"
  fields?: string;          // Comma-separated: "battery.levelPercent,cpu.usagePercent"
}

interface GetTelemetryResponse {
  data: AggregatedTelemetryPoint[];
}

interface AggregatedTelemetryPoint {
  timestamp: string;
  battery?: { avg: number; min: number; max: number };
  cpu?: { avg: number; min: number; max: number };
  // ... other fields as requested
}

// --- Alerts ---

// GET /api/v1/alerts
interface GetAlertsQuery {
  robotId?: string;
  severity?: 'info' | 'warning' | 'critical';
  status?: 'active' | 'acknowledged' | 'resolved';
  from?: string;
  to?: string;
  page?: number;
  limit?: number;
}

interface GetAlertsResponse {
  data: Alert[];
  meta: PaginationMeta;
}

interface Alert {
  alertId: string;
  robotId: string;
  ruleId: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  details: Record<string, unknown>;
  triggeredAt: string;
  acknowledgedAt: string | null;
  acknowledgedBy: string | null;
  resolvedAt: string | null;
}

// POST /api/v1/alerts/:alertId/acknowledge
interface AcknowledgeAlertRequest {
  userId: string;
}

interface AcknowledgeAlertResponse {
  data: Alert;
}

// --- Configuration ---

// GET /api/v1/robots/:robotId/config
interface GetRobotConfigResponse {
  data: RobotConfig;
}

interface RobotConfig {
  robotId: string;
  alertThresholds: AlertThresholds;
  samplingIntervalMs: number;  // e.g., 1000
  reconnectStrategy: ReconnectStrategy;
}

interface AlertThresholds {
  batteryLowPercent: number;       // default 20
  jointTemperatureHighCelsius: number; // default 80
  cpuTemperatureHighCelsius: number;   // default 85
  networkLatencyHighMs: number;        // default 500
  tiltAngleDegrees: number;            // default 45
}

interface ReconnectStrategy {
  maxRetries: number;          // default 5
  baseDelayMs: number;         // default 1000
  backoffMultiplier: number;   // default 2
}

// PUT /api/v1/robots/:robotId/config
interface UpdateRobotConfigRequest {
  alertThresholds?: Partial<AlertThresholds>;
  samplingIntervalMs?: number;
  reconnectStrategy?: Partial<ReconnectStrategy>;
}

interface UpdateRobotConfigResponse {
  data: RobotConfig;
}

// --- Collaboration ---

// GET /api/v1/robots/:robotId/comments
interface GetCommentsQuery {
  page?: number;
  limit?: number;
}

interface GetCommentsResponse {
  data: Comment[];
  meta: PaginationMeta;
}

interface Comment {
  commentId: string;
  robotId: string;
  authorId: string;
  authorName: string;
  content: string;
  mentions: string[];        // User IDs mentioned
  createdAt: string;
  updatedAt: string;
}

// POST /api/v1/robots/:robotId/comments
interface PostCommentRequest {
  content: string;           // Max 2000 chars
  mentions?: string[];       // User IDs
}

interface PostCommentResponse {
  data: Comment;
}

// --- Export ---

// POST /api/v1/export
interface ExportRequest {
  format: 'pdf' | 'xlsx';
  robotIds?: string[];       // All robots if omitted
  from: string;
  to: string;
  includeCharts?: boolean;   // PDF only
  includeAlerts?: boolean;
  includeComments?: boolean;
}

interface ExportResponse {
  data: {
    exportId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    downloadUrl: string | null;  // Available when completed
    expiresAt: string;
  };
}

// GET /api/v1/exports/:exportId
interface GetExportResponse {
  data: {
    exportId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    downloadUrl: string | null;
    expiresAt: string;
  };
}

// ============================================================
// 3. WebSocket Events
// ============================================================

// Client subscribes to robot updates via WebSocket
// Connection: ws://host/ws?token=<jwt>

// Server -> Client events
interface WsTelemetryUpdate {
  type: 'telemetry_update';
  robotId: string;
  telemetry: RobotTelemetry;
}

interface WsAlertEvent {
  type: 'alert';
  alert: Alert;
}

interface WsRobotStatusChange {
  type: 'robot_status_change';
  robotId: string;
  status: 'online' | 'offline' | 'error';
}

interface WsCommentEvent {
  type: 'comment';
  comment: Comment;
}

interface WsMentionEvent {
  type: 'mention';
  commentId: string;
  robotId: string;
  mentionedBy: string;
  content: string;
}

// Client -> Server events
interface WsSubscribe {
  type: 'subscribe';
  robotIds: string[];        // Empty array means all
}

interface WsUnsubscribe {
  type: 'unsubscribe';
  robotIds: string[];
}

interface WsMarkHandling {
  type: 'mark_handling';
  robotId: string;
  userId: string;
  isHandling: boolean;
}

// ============================================================
// 4. Error Contract
// ============================================================

// All API errors follow this structure:
interface ApiError {
  error: {
    code: ErrorCode;
    message: string;
    details?: ErrorDetail[];
  };
  meta: {
    requestId: string;
  };
}

type ErrorCode =
  | 'VALIDATION_ERROR'
  | 'NOT_FOUND'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'RATE_LIMITED'
  | 'INTERNAL_ERROR'
  | 'SERVICE_UNAVAILABLE'
  | 'CONFLICT';

interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

// HTTP Status Code Mapping:
// 200: Success (GET, PUT, PATCH)
// 201: Created (POST)
// 204: No Content (DELETE)
// 400: VALIDATION_ERROR
// 401: UNAUTHORIZED
// 403: FORBIDDEN
// 404: NOT_FOUND
// 409: CONFLICT
// 429: RATE_LIMITED
// 500: INTERNAL_ERROR
// 503: SERVICE_UNAVAILABLE

// ============================================================
// 5. Versioning Strategy
// ============================================================
// - Public API is versioned via URL path prefix: /api/v1/
// - Breaking changes require a new version (v2, etc.)
// - Non-breaking additions (new fields, new endpoints) are allowed within a version
// - Deprecated fields are marked with @deprecated JSDoc and kept for at least one minor release cycle
// - WebSocket protocol version is negotiated via query parameter ?v=1

// ============================================================
// 6. Usage Examples
// ============================================================

// Example 1: Submit telemetry from a robot adapter
// POST /api/v1/robots/rbt-001/telemetry
// Request:
// {
//   "raw": { "batt": 85, "temp": [45.2, 50.1], "cpu": 23, "lat": 12 },
//   "protocol": "json"
// }
// Response:
// {
//   "data": {
//     "accepted": true,
//     "normalized": {
//       "robotId": "rbt-001",
//       "timestamp": "2026-05-30T16:55:12Z",
//       "battery": { "levelPercent": 85, "voltage": 24.5, "isCharging": false },
//       "joints": [
//         { "jointId": "arm_left_shoulder", "temperatureCelsius": 45.2, "isConnected": true, "angleDegrees": 30 },
//         { "jointId": "arm_right_shoulder", "temperatureCelsius": 50.1, "isConnected": true, "angleDegrees": -15 }
//       ],
//       "cpu": { "usagePercent": 23, "temperatureCelsius": 55 },
//       "network": { "latencyMs": 12, "signalStrength": 90, "isConnected": true },
//       "task": null,
//       "location": { "latitude": 40.7128, "longitude": -74.006, "altitudeMeters": 10 },
//       "metadata": {}
//     }
//   }
// }

// Example 2: Fetch historical telemetry
// GET /api/v1/robots/rbt-001/telemetry?from=2026-05-29T00:00:00Z&to=2026-05-30T00:00:00Z&interval=1h&fields=battery.levelPercent,cpu.usagePercent
// Response:
// {
//   "data": [
//     { "timestamp": "2026-05-29T00:00:00Z", "battery": { "avg": 80, "min": 78, "max": 82 }, "cpu": { "avg": 30, "min": 25, "max": 35 } },
//     ...
//   ]
// }

// Example 3: Acknowledge an alert
// POST /api/v1/alerts/alert-123/acknowledge
// Request: { "userId": "user-456" }
// Response: { "data": { "alertId": "alert-123", ..., "acknowledgedAt": "2026-05-30T16:55:12Z", "acknowledgedBy": "user-456", ... } }

// Example 4: WebSocket subscription
// Client sends: { "type": "subscribe", "robotIds": ["rbt-001", "rbt-002"] }
// Server sends: { "type": "telemetry_update", "robotId": "rbt-001", "telemetry": { ... } }

// ============================================================
// 7. Design Rationale
// ============================================================
// - All interfaces are caller-oriented: e.g., `levelPercent` instead of `batteryLevel`.
// - Nullable fields are explicitly `| null`; optional fields use `?`.
// - No god objects: telemetry is decomposed into nested interfaces.
// - Error codes are typed, not stringly-typed.
// - Pagination is consistent across list endpoints.
// - WebSocket events are typed and versioned.
// - Breaking changes require a new API version.
