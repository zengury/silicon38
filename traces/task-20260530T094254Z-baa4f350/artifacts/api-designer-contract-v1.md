// ============================================================
// RoboEase API Contract — TypeScript Interfaces & Types
// Version: 1.0.0
// Design Principles:
// - Caller-oriented naming: names reflect what the caller wants, not the implementer.
// - Explicit nullability: every field is either required, optional, or nullable.
// - Scoped inputs: no god objects; each function receives only what it needs.
// - Typed errors: all error conditions are represented as discriminated unions.
// - Usage without reading implementation: contracts are self-documenting.
// ============================================================

// ──────────────────────────────────────────────────────────────
// Shared / Common Types
// ──────────────────────────────────────────────────────────────

/** ISO 8601 datetime string (e.g., "2025-06-30T09:42:54Z") */
export type DateTimeString = string;

/** UUID v4 string */
export type UUID = string;

/** Pagination cursor (opaque base64-encoded string) */
export type Cursor = string;

/** Generic paginated response envelope */
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    nextCursor: Cursor | null;
    hasMore: boolean;
  };
}

// ──────────────────────────────────────────────────────────────
// Auth Module
// ──────────────────────────────────────────────────────────────

/** POST /api/v1/auth/login */
export interface LoginRequest {
  /** User's email address */
  email: string;
  /** User's password (plaintext, transmitted over HTTPS) */
  password: string;
}

export interface LoginResponse {
  /** JWT access token */
  accessToken: string;
  /** Token type (always "Bearer") */
  tokenType: string;
  /** Token expiration in seconds from now */
  expiresIn: number;
  /** Authenticated user summary */
  user: UserSummary;
}

/** POST /api/v1/auth/refresh */
export interface RefreshTokenRequest {
  /** Valid refresh token */
  refreshToken: string;
}

export interface RefreshTokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

/** POST /api/v1/auth/logout */
export interface LogoutRequest {
  /** Refresh token to invalidate */
  refreshToken: string;
}

// ──────────────────────────────────────────────────────────────
// User Module
// ──────────────────────────────────────────────────────────────

export interface UserSummary {
  id: UUID;
  email: string;
  displayName: string;
  avatarUrl: string | null;
  role: UserRole;
}

export type UserRole = "admin" | "operator" | "viewer";

/** GET /api/v1/users/me */
export type GetCurrentUserResponse = UserSummary;

/** PATCH /api/v1/users/me */
export interface UpdateCurrentUserRequest {
  displayName?: string;
  avatarUrl?: string | null;
}

export type UpdateCurrentUserResponse = UserSummary;

/** GET /api/v1/users (admin only) */
export interface ListUsersQuery {
  page?: number;
  pageSize?: number;
  role?: UserRole;
  search?: string;
}

export interface ListUsersResponse {
  data: UserSummary[];
  total: number;
  page: number;
  pageSize: number;
}

/** POST /api/v1/users (admin only) */
export interface CreateUserRequest {
  email: string;
  password: string;
  displayName: string;
  role: UserRole;
}

export type CreateUserResponse = UserSummary;

/** DELETE /api/v1/users/:id (admin only) */
export type DeleteUserResponse = { success: true };

// ──────────────────────────────────────────────────────────────
// Robot Module
// ──────────────────────────────────────────────────────────────

export type RobotStatus = "online" | "offline" | "busy" | "error" | "charging";

export interface RobotSummary {
  id: UUID;
  name: string;
  model: string;
  status: RobotStatus;
  batteryLevel: number; // 0–100
  lastSeenAt: DateTimeString | null;
}

/** GET /api/v1/robots */
export interface ListRobotsQuery {
  status?: RobotStatus;
  search?: string;
  cursor?: Cursor;
  limit?: number; // default 20, max 100
}

export type ListRobotsResponse = PaginatedResponse<RobotSummary>;

/** GET /api/v1/robots/:id */
export interface GetRobotResponse extends RobotSummary {
  ipAddress: string | null;
  firmwareVersion: string;
  connectedSince: DateTimeString | null;
  capabilities: string[];
}

/** POST /api/v1/robots/:id/command */
export interface SendRobotCommandRequest {
  /** Command name (e.g., "move", "stop", "dock") */
  command: string;
  /** Command-specific parameters */
  parameters?: Record<string, unknown>;
}

export interface SendRobotCommandResponse {
  /** Unique command ID for tracking */
  commandId: UUID;
  /** Whether the command was accepted (not necessarily executed) */
  accepted: boolean;
}

/** GET /api/v1/robots/:id/commands/:commandId */
export type CommandStatus = "pending" | "in_progress" | "completed" | "failed";

export interface GetCommandStatusResponse {
  commandId: UUID;
  status: CommandStatus;
  result: unknown | null;
  error: CommandError | null;
  createdAt: DateTimeString;
  completedAt: DateTimeString | null;
}

export interface CommandError {
  code: string;
  message: string;
}

/** GET /api/v1/robots/:id/telemetry (WebSocket upgrade) */
export interface RobotTelemetryMessage {
  type: "telemetry";
  robotId: UUID;
  timestamp: DateTimeString;
  batteryLevel: number;
  position: { x: number; y: number; theta: number } | null;
  status: RobotStatus;
}

// ──────────────────────────────────────────────────────────────
// Video Module
// ──────────────────────────────────────────────────────────────

/** GET /api/v1/robots/:id/stream (WebSocket upgrade) */
export interface VideoStreamMessage {
  type: "video_frame";
  robotId: UUID;
  /** JPEG-encoded frame as base64 */
  frame: string;
  timestamp: DateTimeString;
}

/** POST /api/v1/robots/:id/stream/control */
export interface StreamControlRequest {
  action: "start" | "stop" | "pause" | "resume";
  /** Optional stream quality (1–100) */
  quality?: number;
}

export type StreamControlResponse = { success: true };

// ──────────────────────────────────────────────────────────────
// Admin Module
// ──────────────────────────────────────────────────────────────

/** GET /api/v1/admin/dashboard */
export interface DashboardResponse {
  totalRobots: number;
  onlineRobots: number;
  totalUsers: number;
  activeUsersToday: number;
  recentAlerts: AlertSummary[];
}

export interface AlertSummary {
  id: UUID;
  severity: "info" | "warning" | "critical";
  message: string;
  createdAt: DateTimeString;
  acknowledged: boolean;
}

/** GET /api/v1/admin/logs */
export interface ListLogsQuery {
  level?: "debug" | "info" | "warn" | "error";
  startDate?: DateTimeString;
  endDate?: DateTimeString;
  cursor?: Cursor;
  limit?: number;
}

export interface LogEntry {
  id: UUID;
  timestamp: DateTimeString;
  level: string;
  module: string;
  message: string;
  metadata: Record<string, unknown> | null;
}

export type ListLogsResponse = PaginatedResponse<LogEntry>;

// ──────────────────────────────────────────────────────────────
// Error Contract
// ──────────────────────────────────────────────────────────────

/** Standard API error response body */
export interface ApiError {
  error: {
    /** Machine-readable error code */
    code: ErrorCode;
    /** Human-readable error message */
    message: string;
    /** Detailed validation errors (if applicable) */
    details?: ValidationErrorDetail[];
    /** Unique request ID for tracing */
    requestId: string;
    /** ISO 8601 timestamp */
    timestamp: DateTimeString;
  };
}

export type ErrorCode =
  | "VALIDATION_ERROR"
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "RATE_LIMIT_EXCEEDED"
  | "INTERNAL_ERROR"
  | "COMMAND_FAILED"
  | "ROBOT_OFFLINE"
  | "STREAM_UNAVAILABLE";

export interface ValidationErrorDetail {
  field: string;
  code: string;
  message: string;
}

/** HTTP status codes used by the API */
export type HttpStatus =
  | 200
  | 201
  | 204
  | 400
  | 401
  | 403
  | 404
  | 409
  | 422
  | 429
  | 500;

// ──────────────────────────────────────────────────────────────
// WebSocket Event Types (for real-time updates)
// ──────────────────────────────────────────────────────────────

export type WsEvent =
  | { type: "robot_status_change"; robotId: UUID; newStatus: RobotStatus }
  | { type: "robot_telemetry"; robotId: UUID; data: RobotTelemetryMessage }
  | { type: "alert"; alert: AlertSummary }
  | { type: "command_update"; commandId: UUID; status: CommandStatus };

// ──────────────────────────────────────────────────────────────
// Usage Examples (demonstrate correct usage without reading implementation)
// ──────────────────────────────────────────────────────────────

// Example 1: Login
// const loginReq: LoginRequest = { email: "user@example.com", password: "secret" };
// const loginRes: LoginResponse = await api.post("/auth/login", loginReq);
// localStorage.setItem("token", loginRes.accessToken);

// Example 2: List robots with pagination
// const robots: ListRobotsResponse = await api.get("/robots", { status: "online", limit: 20 });
// for (const robot of robots.data) { console.log(robot.name); }

// Example 3: Send command to robot
// const cmdReq: SendRobotCommandRequest = { command: "dock", parameters: { stationId: "A1" } };
// const cmdRes: SendRobotCommandResponse = await api.post(`/robots/${robotId}/command`, cmdReq);
// const status: GetCommandStatusResponse = await api.get(`/robots/${robotId}/commands/${cmdRes.commandId}`);

// Example 4: Handle error
// try { ... } catch (err) {
//   const apiErr: ApiError = err.response.data;
//   if (apiErr.error.code === "VALIDATION_ERROR") { ... }
// }
