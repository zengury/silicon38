# RoboEase API Contract
# FastAPI + Pydantic v2
# Version: 1.0.0
# Base URL: /api/v1

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, UUID4

# ──────────────────────────────────────────────
# Error Contract
# ──────────────────────────────────────────────

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="Field that caused the error, if applicable")
    message: str = Field(..., description="Human-readable error description")
    code: Optional[str] = Field(None, description="Machine-readable error code for this detail")

class ErrorResponse(BaseModel):
    error: ErrorCode = Field(..., description="Top-level error code")
    message: str = Field(..., description="Human-readable error message")
    details: List[ErrorDetail] = Field(default_factory=list, description="List of specific error details")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")

# ──────────────────────────────────────────────
# Authentication & Authorization
# ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100, description="User login name")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Access token lifetime in seconds")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")

class TokenIntrospectResponse(BaseModel):
    active: bool = Field(..., description="Whether the token is active")
    user_id: Optional[UUID4] = Field(None, description="User ID if token is valid")
    roles: List[str] = Field(default_factory=list, description="User roles")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")

# ──────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    role: UserRole = Field(UserRole.VIEWER, description="Initial user role")

class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated display name")
    email: Optional[EmailStr] = Field(None, description="Updated email")
    role: Optional[UserRole] = Field(None, description="Updated role")
    status: Optional[UserStatus] = Field(None, description="Updated status")

class UserResponse(BaseModel):
    id: UUID4 = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    display_name: str = Field(..., description="Display name")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class PaginatedUsersResponse(BaseModel):
    items: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., ge=0, description="Total number of users matching the query")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

# ──────────────────────────────────────────────
# Robot Management
# ──────────────────────────────────────────────

class RobotStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class RobotType(str, Enum):
    STAR_WALKER = "star_walker"
    PLANNING = "planning"
    CUSTOM = "custom"

class CreateRobotRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Robot display name")
    robot_type: RobotType = Field(..., description="Type of robot")
    description: Optional[str] = Field(None, max_length=500, description="Robot description")
    config: Optional[dict] = Field(None, description="Robot-specific configuration as key-value pairs")

class UpdateRobotRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated robot name")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    config: Optional[dict] = Field(None, description="Updated configuration")
    status: Optional[RobotStatus] = Field(None, description="Updated status")

class RobotResponse(BaseModel):
    id: UUID4 = Field(..., description="Unique robot identifier")
    name: str = Field(..., description="Robot display name")
    robot_type: RobotType = Field(..., description="Type of robot")
    status: RobotStatus = Field(..., description="Current robot status")
    description: Optional[str] = Field(None, description="Robot description")
    config: dict = Field(default_factory=dict, description="Robot configuration")
    created_by: UUID4 = Field(..., description="User ID who created the robot")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_online_at: Optional[datetime] = Field(None, description="Last time the robot was online")

class PaginatedRobotsResponse(BaseModel):
    items: List[RobotResponse] = Field(..., description="List of robots")
    total: int = Field(..., ge=0, description="Total number of robots matching the query")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

# ──────────────────────────────────────────────
# Robot Control & Telemetry
# ──────────────────────────────────────────────

class CommandType(str, Enum):
    MOVE = "move"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    HOME = "home"
    CUSTOM = "custom"

class SendCommandRequest(BaseModel):
    command: CommandType = Field(..., description="Command to execute")
    parameters: Optional[dict] = Field(None, description="Command parameters as key-value pairs")
    timeout: Optional[int] = Field(None, ge=1, le=300, description="Command timeout in seconds")

class CommandResponse(BaseModel):
    command_id: UUID4 = Field(..., description="Unique command identifier")
    status: str = Field(..., description="Command status: accepted, queued, executing, completed, failed")
    message: Optional[str] = Field(None, description="Status message")

class TelemetryData(BaseModel):
    robot_id: UUID4 = Field(..., description="Robot identifier")
    timestamp: datetime = Field(..., description="Telemetry timestamp")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Battery percentage")
    position: Optional[dict] = Field(None, description="Position coordinates (x, y, z)")
    orientation: Optional[dict] = Field(None, description="Orientation (roll, pitch, yaw)")
    speed: Optional[float] = Field(None, ge=0, description="Current speed in m/s")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    error_code: Optional[str] = Field(None, description="Error code if any")
    additional_data: Optional[dict] = Field(None, description="Additional telemetry data")

# ──────────────────────────────────────────────
# WebSocket Events (for real-time communication)
# ──────────────────────────────────────────────

class WebSocketEventType(str, Enum):
    TELEMETRY = "telemetry"
    COMMAND_STATUS = "command_status"
    ROBOT_STATUS = "robot_status"
    ALERT = "alert"
    ERROR = "error"

class WebSocketEvent(BaseModel):
    event_type: WebSocketEventType = Field(..., description="Type of event")
    robot_id: UUID4 = Field(..., description="Robot identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: dict = Field(..., description="Event payload")

# ──────────────────────────────────────────────
# Health & Monitoring
# ──────────────────────────────────────────────

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheckResponse(BaseModel):
    status: HealthStatus = Field(..., description="Overall service health")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    database: HealthStatus = Field(..., description="Database connectivity status")
    redis: Optional[HealthStatus] = Field(None, description="Redis connectivity status")
    mqtt: Optional[HealthStatus] = Field(None, description="MQTT broker connectivity status")

# ──────────────────────────────────────────────
# Pagination & Filtering
# ──────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", pattern=r"^(asc|desc)$", description="Sort order: asc or desc")

# ──────────────────────────────────────────────
# API Endpoints Summary (for documentation)
# ──────────────────────────────────────────────
#
# POST   /api/v1/auth/login              -> LoginRequest        -> TokenResponse
# POST   /api/v1/auth/refresh            -> RefreshTokenRequest -> TokenResponse
# POST   /api/v1/auth/logout             -> (empty)             -> 204 No Content
# GET    /api/v1/auth/introspect         -> (query: token)      -> TokenIntrospectResponse
#
# GET    /api/v1/users                   -> PaginationParams    -> PaginatedUsersResponse
# POST   /api/v1/users                   -> CreateUserRequest   -> UserResponse (201)
# GET    /api/v1/users/{user_id}         -> (path param)        -> UserResponse
# PATCH  /api/v1/users/{user_id}         -> UpdateUserRequest   -> UserResponse
# DELETE /api/v1/users/{user_id}         -> (path param)        -> 204 No Content
#
# GET    /api/v1/robots                  -> PaginationParams    -> PaginatedRobotsResponse
# POST   /api/v1/robots                  -> CreateRobotRequest  -> RobotResponse (201)
# GET    /api/v1/robots/{robot_id}       -> (path param)        -> RobotResponse
# PATCH  /api/v1/robots/{robot_id}       -> UpdateRobotRequest  -> RobotResponse
# DELETE /api/v1/robots/{robot_id}       -> (path param)        -> 204 No Content
# POST   /api/v1/robots/{robot_id}/command -> SendCommandRequest -> CommandResponse
# GET    /api/v1/robots/{robot_id}/telemetry -> (query: since)   -> List[TelemetryData]
#
# WS     /api/v1/ws/robots/{robot_id}   -> WebSocket connection -> WebSocketEvent
#
# GET    /api/v1/health                  -> (empty)             -> HealthCheckResponse
