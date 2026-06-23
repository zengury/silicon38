// ============================================================
// RoboEase API Contract v1.0
// TypeScript interfaces defining the public API surface.
// Versioning: URL-based (e.g., /api/v1/...)
// ============================================================

// ── Common Types ─────────────────────────────────────────────────────

/** ISO 8601 timestamp string */
export type ISODateTime = string;

/** UUID v4 */
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

// ── Error Contract ───────────────────────────────────────────────────

/** Standard error response body */
export interface ApiError {
  error: {
    code: ErrorCode;
    message: string;
    details?: ErrorDetail[];
    requestId: UUID;
    timestamp: ISODateTime;
  };
}

export interface ErrorDetail {
  field: string;
  code: string;
  message: string;
}

export type ErrorCode =
  | 'VALIDATION_ERROR'
  | 'AUTHENTICATION_ERROR'
  | 'AUTHORIZATION_ERROR'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'RATE_LIMIT_EXCEEDED'
  | 'INTERNAL_ERROR';

// ── Authentication ───────────────────────────────────────────────────

/** POST /api/v1/auth/login */
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number; // seconds
  user: UserProfile;
}

/** POST /api/v1/auth/refresh */
export interface RefreshTokenRequest {
  refreshToken: string;
}

export interface RefreshTokenResponse {
  accessToken: string;
  expiresIn: number;
}

/** POST /api/v1/auth/logout */
export interface LogoutRequest {
  refreshToken: string;
}

// ── User Profile ─────────────────────────────────────────────────────

export interface UserProfile {
  id: UUID;
  username: string;
  email: string;
  avatarUrl: string | null;
  roles: string[];
  createdAt: ISODateTime;
}

/** GET /api/v1/users/me */
export type GetCurrentUserResponse = UserProfile;

/** PUT /api/v1/users/me */
export interface UpdateUserRequest {
  email?: string;
  avatarUrl?: string | null;
}

export type UpdateUserResponse = UserProfile;

// ── Robots ───────────────────────────────────────────────────────────

export type RobotStatus = 'online' | 'offline' | 'error' | 'busy';

export interface Robot {
  id: UUID;
  name: string;
  model: string;
  status: RobotStatus;
  lastSeenAt: ISODateTime | null;
  location: {
    latitude: number;
    longitude: number;
  } | null;
  metadata: Record<string, string>;
  createdAt: ISODateTime;
}

/** GET /api/v1/robots */
export interface ListRobotsParams {
  status?: RobotStatus;
  search?: string;
  cursor?: Cursor;
  limit?: number; // default 20, max 100
}

export type ListRobotsResponse = PaginatedResponse<Robot>;

/** GET /api/v1/robots/:id */
export type GetRobotResponse = Robot;

/** POST /api/v1/robots */
export interface CreateRobotRequest {
  name: string;
  model: string;
  metadata?: Record<string, string>;
}

export type CreateRobotResponse = Robot;

/** PUT /api/v1/robots/:id */
export interface UpdateRobotRequest {
  name?: string;
  metadata?: Record<string, string>;
}

export type UpdateRobotResponse = Robot;

/** DELETE /api/v1/robots/:id */
export type DeleteRobotResponse = void;

// ── Robot Commands ───────────────────────────────────────────────────

export type CommandType = 'move' | 'stop' | 'pause' | 'resume' | 'custom';

export interface RobotCommand {
  id: UUID;
  robotId: UUID;
  type: CommandType;
  payload: Record<string, unknown>;
  status: 'pending' | 'sent' | 'delivered' | 'acknowledged' | 'failed';
  createdAt: ISODateTime;
  acknowledgedAt: ISODateTime | null;
}

/** POST /api/v1/robots/:id/commands */
export interface SendCommandRequest {
  type: CommandType;
  payload: Record<string, unknown>;
}

export type SendCommandResponse = RobotCommand;

/** GET /api/v1/robots/:id/commands */
export interface ListRobotCommandsParams {
  status?: RobotCommand['status'];
  cursor?: Cursor;
  limit?: number;
}

export type ListRobotCommandsResponse = PaginatedResponse<RobotCommand>;

// ── Telemetry ────────────────────────────────────────────────────────

export interface TelemetryPoint {
  timestamp: ISODateTime;
  batteryLevel: number | null; // percentage 0-100
  cpuUsage: number | null;     // percentage 0-100
  memoryUsage: number | null;  // percentage 0-100
  temperature: number | null;  // celsius
  location: {
    latitude: number;
    longitude: number;
  } | null;
}

/** GET /api/v1/robots/:id/telemetry */
export interface ListTelemetryParams {
  from?: ISODateTime;
  to?: ISODateTime;
  cursor?: Cursor;
  limit?: number;
}

export type ListTelemetryResponse = PaginatedResponse<TelemetryPoint>;

// ── WebSocket Events (via STOMP over WebSocket) ──────────────────────

/** Topic: /topic/robots/:id/telemetry */
export interface TelemetryEvent {
  type: 'telemetry';
  robotId: UUID;
  data: TelemetryPoint;
}

/** Topic: /topic/robots/:id/status */
export interface RobotStatusEvent {
  type: 'status_change';
  robotId: UUID;
  previousStatus: RobotStatus;
  newStatus: RobotStatus;
  timestamp: ISODateTime;
}

/** Topic: /topic/robots/:id/commands */
export interface CommandAckEvent {
  type: 'command_ack';
  commandId: UUID;
  robotId: UUID;
  status: RobotCommand['status'];
  timestamp: ISODateTime;
}

// ── Admin: Users ─────────────────────────────────────────────────────

export interface AdminUser extends UserProfile {
  isActive: boolean;
  lastLoginAt: ISODateTime | null;
}

/** GET /api/v1/admin/users */
export interface ListAdminUsersParams {
  search?: string;
  role?: string;
  isActive?: boolean;
  cursor?: Cursor;
  limit?: number;
}

export type ListAdminUsersResponse = PaginatedResponse<AdminUser>;

/** POST /api/v1/admin/users */
export interface CreateAdminUserRequest {
  username: string;
  email: string;
  password: string;
  roles: string[];
}

export type CreateAdminUserResponse = AdminUser;

/** PUT /api/v1/admin/users/:id */
export interface UpdateAdminUserRequest {
  email?: string;
  roles?: string[];
  isActive?: boolean;
}

export type UpdateAdminUserResponse = AdminUser;

/** DELETE /api/v1/admin/users/:id */
export type DeleteAdminUserResponse = void;

// ── Admin: Roles ─────────────────────────────────────────────────────

export interface Role {
  id: UUID;
  name: string;
  description: string;
  permissions: string[];
  createdAt: ISODateTime;
}

/** GET /api/v1/admin/roles */
export type ListRolesResponse = Role[];

/** POST /api/v1/admin/roles */
export interface CreateRoleRequest {
  name: string;
  description: string;
  permissions: string[];
}

export type CreateRoleResponse = Role;

/** PUT /api/v1/admin/roles/:id */
export interface UpdateRoleRequest {
  name?: string;
  description?: string;
  permissions?: string[];
}

export type UpdateRoleResponse = Role;

/** DELETE /api/v1/admin/roles/:id */
export type DeleteRoleResponse = void;

// ── Admin: System Logs ───────────────────────────────────────────────

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface SystemLog {
  id: UUID;
  timestamp: ISODateTime;
  level: LogLevel;
  source: string;
  message: string;
  metadata: Record<string, unknown>;
}

/** GET /api/v1/admin/logs */
export interface ListLogsParams {
  level?: LogLevel;
  source?: string;
  from?: ISODateTime;
  to?: ISODateTime;
  cursor?: Cursor;
  limit?: number;
}

export type ListLogsResponse = PaginatedResponse<SystemLog>;

// ── Health Check ─────────────────────────────────────────────────────

/** GET /api/v1/health */
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'down';
  version: string;
  uptime: number; // seconds
  checks: {
    database: 'ok' | 'down';
    redis: 'ok' | 'down';
    emqx: 'ok' | 'down';
    minio: 'ok' | 'down';
  };
}

// ── Usage Examples ───────────────────────────────────────────────────

/*
 * Example 1: Login and fetch robots
 *
 * const loginResp = await fetch('/api/v1/auth/login', {
 *   method: 'POST',
 *   headers: { 'Content-Type': 'application/json' },
 *   body: JSON.stringify({ username: 'admin', password: 'secret' } as LoginRequest),
 * });
 * const { accessToken } = await loginResp.json() as LoginResponse;
 *
 * const robotsResp = await fetch('/api/v1/robots?limit=10', {
 *   headers: { Authorization: `Bearer ${accessToken}` },
 * });
 * const robots = await robotsResp.json() as ListRobotsResponse;
 * console.log(robots.data);
 *
 * Example 2: Send command to robot
 *
 * const cmdResp = await fetch('/api/v1/robots/abc-123/commands', {
 *   method: 'POST',
 *   headers: {
 *     'Content-Type': 'application/json',
 *     Authorization: `Bearer ${accessToken}`,
 *   },
 *   body: JSON.stringify({ type: 'move', payload: { x: 10, y: 20 } } as SendCommandRequest),
 * });
 * const command = await cmdResp.json() as SendCommandResponse;
 *
 * Example 3: Handle error
 *
 * if (!cmdResp.ok) {
 *   const err = await cmdResp.json() as ApiError;
 *   console.error(err.error.message);
 * }
 */
