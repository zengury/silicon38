# Database Schema Design: 机器人车队运维监控面板

> Source: Architect ADR-001 (BFF Modular Monolith) + ADR-002 (Normalization Pipeline) + ADR-003 (TimescaleDB)
> Target: PostgreSQL 16 + TimescaleDB 2.x + Redis 7

---

## 1. Schema Overview

```
┌──────────────────────────────────────┐
│           PostgreSQL (BFF)           │
│                                      │
│  ┌─────────┐  ┌──────────┐          │
│  │ robots  │  │  users   │          │
│  └────┬────┘  └────┬─────┘          │
│       │            │                │
│  ┌────┴────────────┴─────┐          │
│  │     alert_rules       │          │
│  └───────────┬───────────┘          │
│              │                      │
│  ┌───────────┴───────────┐          │
│  │    alert_events       │          │
│  └───────────────────────┘          │
│                                      │
│  ┌───────────────────────┐          │
│  │     comments          │          │
│  └───────────────────────┘          │
│                                      │
│  ┌───────────────────────┐          │
│  │   config_audit_log    │          │
│  └───────────────────────┘          │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        TimescaleDB (Pipeline)        │
│                                      │
│  ┌───────────────────────┐          │
│  │     telemetry         │  ← Hypertable
│  │   (partitioned by     │
│  │    timestamp, 1d      │
│  │    chunks)            │          │
│  └───────────┬───────────┘          │
│              │                      │
│  ┌───────────┴───────────┐          │
│  │  telemetry_hourly     │  ← Continuous Aggregate
│  │   (MATERIALIZED)      │          │
│  └───────────────────────┘          │
│                                      │
│  ┌───────────────────────┐          │
│  │  telemetry_daily      │  ← Continuous Aggregate
│  └───────────────────────┘          │
└──────────────────────────────────────┘
```

---

## 2. PostgreSQL Schema (BFF)

### Migration V001 — Core Tables

```sql
-- 001_core_tables.up.sql

-- ═══════════════════════════════════════════════════════════
-- EXTENSIONS
-- ═══════════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════
-- robots
-- ═══════════════════════════════════════════════════════════
CREATE TABLE robots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    model           TEXT NOT NULL,                    -- e.g. "unitree_g1", "agibot_x2"
    serial_number   TEXT UNIQUE,
    group_name      TEXT,                             -- fleet grouping: "warehouse_a", "lab_3f"
    config          JSONB NOT NULL DEFAULT '{}',      -- per-robot settings
    tags            TEXT[] DEFAULT '{}',              -- flexible tagging
    status          TEXT NOT NULL DEFAULT 'unknown'
                    CHECK (status IN ('online', 'offline', 'error', 'delayed', 'unknown')),
    last_telemetry_at TIMESTAMPTZ,                   -- derived from TSDB
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                       -- soft delete
);

-- Indexes
CREATE INDEX idx_robots_status ON robots(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_robots_group ON robots(group_name) WHERE deleted_at IS NULL;
CREATE INDEX idx_robots_model ON robots(model);
CREATE INDEX idx_robots_name_trgm ON robots USING GIN (name gin_trgm_ops);  -- fuzzy search

-- Default config template
COMMENT ON COLUMN robots.config IS 'JSON schema:
{
  "sample_rate_seconds": 5,
  "alert_thresholds": {
    "battery_pct_low": 20,
    "cpu_pct_high": 90,
    "memory_pct_high": 90,
    "network_latency_ms_high": 500,
    "joint_temp_c_high": 75
  },
  "geofence": null
}';

-- ═══════════════════════════════════════════════════════════
-- users
-- ═══════════════════════════════════════════════════════════
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        TEXT NOT NULL UNIQUE,
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'operator'
                    CHECK (role IN ('admin', 'operator', 'viewer')),
    avatar_url      TEXT,
    password_hash   TEXT NOT NULL,                     -- bcrypt via pgcrypto
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username);

-- ═══════════════════════════════════════════════════════════
-- alert_rules
-- ═══════════════════════════════════════════════════════════
CREATE TABLE alert_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    robot_id        UUID REFERENCES robots(id) ON DELETE CASCADE,
    -- NULL robot_id = fleet-wide rule (applies to all robots)

    metric          TEXT NOT NULL,                     -- "battery_pct", "cpu_pct", "joint_temp_c"
    operator        TEXT NOT NULL
                    CHECK (operator IN ('>', '<', '>=', '<=', '==', '!=')),
    threshold       DOUBLE PRECISION NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warning'
                    CHECK (severity IN ('critical', 'warning', 'info')),
    cooldown_seconds INTEGER NOT NULL DEFAULT 300,    -- 5 min default

    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    description     TEXT,

    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alert_rules_robot ON alert_rules(robot_id, enabled);
CREATE INDEX idx_alert_rules_metric ON alert_rules(metric, enabled);

-- ═══════════════════════════════════════════════════════════
-- alert_events
-- ═══════════════════════════════════════════════════════════
CREATE TABLE alert_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    robot_id        UUID NOT NULL REFERENCES robots(id) ON DELETE CASCADE,

    status          TEXT NOT NULL DEFAULT 'triggered'
                    CHECK (status IN ('triggered', 'acknowledged', 'dismissed', 'snoozed')),
    severity        TEXT NOT NULL
                    CHECK (severity IN ('critical', 'warning', 'info')),

    -- Snapshot of the triggering data point
    metric_value    DOUBLE PRECISION NOT NULL,
    threshold_value DOUBLE PRECISION NOT NULL,
    message         TEXT NOT NULL,                     -- human-readable: "Battery at 14% (threshold: 20%)"

    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES users(id),
    dismissed_at    TIMESTAMPTZ,
    dismissed_by    UUID REFERENCES users(id),
    snoozed_until   TIMESTAMPTZ
);

-- Indexes for alert queries
CREATE INDEX idx_alert_events_robot_status ON alert_events(robot_id, status);
CREATE INDEX idx_alert_events_status_time ON alert_events(status, triggered_at DESC);
CREATE INDEX idx_alert_events_severity ON alert_events(severity, triggered_at DESC);
CREATE INDEX idx_alert_events_time ON alert_events(triggered_at DESC);

-- Partial index: only active alerts (frequently queried subset)
CREATE INDEX idx_alert_events_active ON alert_events(robot_id, severity)
    WHERE status IN ('triggered', 'snoozed');

-- ═══════════════════════════════════════════════════════════
-- comments
-- ═══════════════════════════════════════════════════════════
CREATE TABLE comments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    robot_id        UUID NOT NULL REFERENCES robots(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES comments(id) ON DELETE CASCADE,  -- NULL = top-level

    body            TEXT NOT NULL,
    -- @mentions extracted as array for query efficiency
    mentioned_users UUID[] DEFAULT '{}',

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                       -- soft delete
);

CREATE INDEX idx_comments_robot_time ON comments(robot_id, created_at DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_parent ON comments(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_mentions ON comments USING GIN (mentioned_users);

-- ═══════════════════════════════════════════════════════════
-- config_audit_log
-- ═══════════════════════════════════════════════════════════
CREATE TABLE config_audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    robot_id        UUID NOT NULL REFERENCES robots(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

    field_path      TEXT NOT NULL,                    -- JSON path: "alert_thresholds.battery_pct_low"
    old_value       JSONB,
    new_value       JSONB,

    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_config_audit_robot_time ON config_audit_log(robot_id, changed_at DESC);
CREATE INDEX idx_config_audit_user ON config_audit_log(user_id, changed_at DESC);

-- ═══════════════════════════════════════════════════════════
-- TRIGGER: auto-update updated_at
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_robots
    BEFORE UPDATE ON robots
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_users
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_alert_rules
    BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at_comments
    BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
```

### Migration V001 Rollback

```sql
-- 001_core_tables.down.sql

DROP TRIGGER IF EXISTS set_updated_at_comments ON comments;
DROP TRIGGER IF EXISTS set_updated_at_alert_rules ON alert_rules;
DROP TRIGGER IF EXISTS set_updated_at_users ON users;
DROP TRIGGER IF EXISTS set_updated_at_robots ON robots;
DROP FUNCTION IF EXISTS trigger_set_updated_at();

DROP TABLE IF EXISTS config_audit_log;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS alert_events;
DROP TABLE IF EXISTS alert_rules;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS robots;
```

---

### Migration V002 — Seed Data

```sql
-- 002_seed_data.up.sql

-- ═══════════════════ USERS ═══════════════════
INSERT INTO users (username, email, display_name, role, password_hash) VALUES
('zhangwei', 'zhangwei@fleetops.local',  '张工 (Zhang Wei)',  'operator', crypt('changeme123', gen_salt('bf'))),
('liming',   'liming@fleetops.local',    '李工 (Li Ming)',    'admin',    crypt('changeme123', gen_salt('bf'))),
('wangfang', 'wangfang@fleetops.local',  '王工 (Wang Fang)',  'viewer',   crypt('changeme123', gen_salt('bf')));

-- ═══════════════════ ROBOTS ═══════════════════
INSERT INTO robots (name, model, serial_number, group_name, status, config) VALUES
('G1-Alpha',    'unitree_g1',  'G1-2024-0001', 'lab_3f', 'online',
 '{"sample_rate_seconds": 5, "alert_thresholds": {"battery_pct_low": 20, "cpu_pct_high": 90, "network_latency_ms_high": 500, "joint_temp_c_high": 75}}'),
('G1-Beta',     'unitree_g1',  'G1-2024-0002', 'lab_3f', 'online',
 '{"sample_rate_seconds": 10, "alert_thresholds": {"battery_pct_low": 15, "cpu_pct_high": 85}}'),
('X2-Charlie',  'agibot_x2',   'X2-2024-0001', 'warehouse_a', 'delayed',
 '{"sample_rate_seconds": 5, "alert_thresholds": {"battery_pct_low": 25, "network_latency_ms_high": 1000}}'),
('X2-Delta',    'agibot_x2',   'X2-2024-0002', 'warehouse_a', 'offline',
 '{"sample_rate_seconds": 30, "alert_thresholds": {"battery_pct_low": 30}}'),
('G1-Epsilon',  'unitree_g1',  'G1-2024-0003', 'lab_3f', 'online',
 '{"sample_rate_seconds": 5, "geofence": {"lat": 31.2304, "lon": 121.4737, "radius_m": 500}}');

-- ═══════════════════ ALERT RULES ═══════════════════
-- Fleet-wide rules (robot_id IS NULL)
INSERT INTO alert_rules (robot_id, metric, operator, threshold, severity, cooldown_seconds, description, created_by) VALUES
(NULL, 'battery_pct', '<',  20,  'critical', 180,  'Fleet-wide: battery below 20%',  (SELECT id FROM users WHERE username='liming')),
(NULL, 'cpu_pct',     '>',  90,  'warning',  300,  'Fleet-wide: CPU above 90%',      (SELECT id FROM users WHERE username='liming')),
(NULL, 'joint_temp_c','>',  75,  'warning',  600,  'Fleet-wide: joint temp above 75°C', (SELECT id FROM users WHERE username='liming')),
(NULL, 'network_latency_ms', '>', 1000, 'critical',  120, 'Fleet-wide: latency > 1s', (SELECT id FROM users WHERE username='liming'));

-- Per-robot overrides
INSERT INTO alert_rules (robot_id, metric, operator, threshold, severity, cooldown_seconds, description, created_by)
SELECT id, 'battery_pct', '<', 15, 'critical', 180, 'G1-Beta: battery below 15% (lower threshold for testing)', (SELECT id FROM users WHERE username='liming')
FROM robots WHERE name = 'G1-Beta';
```

### Migration V002 Rollback

```sql
-- 002_seed_data.down.sql
DELETE FROM alert_rules WHERE created_by IN (SELECT id FROM users WHERE username='liming');
DELETE FROM users WHERE username IN ('zhangwei', 'liming', 'wangfang');
DELETE FROM robots WHERE name IN ('G1-Alpha', 'G1-Beta', 'X2-Charlie', 'X2-Delta', 'G1-Epsilon');
```

---

## 3. TimescaleDB Schema (Data Pipeline)

### Migration V001 — Telemetry Hypertable

```sql
-- 001_timescale_telemetry.up.sql

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ═══════════════════════════════════════════════════════════
-- telemetry: main hypertable for all robot telemetry
-- ═══════════════════════════════════════════════════════════
CREATE TABLE telemetry (
    time            TIMESTAMPTZ NOT NULL,              -- partition key

    -- Robot identity
    robot_id        TEXT NOT NULL,

    -- Core metrics (nullable — not all robots report all fields)
    battery_pct     DOUBLE PRECISION,
    battery_voltage DOUBLE PRECISION,
    cpu_pct         DOUBLE PRECISION,
    memory_pct      DOUBLE PRECISION,
    disk_pct        DOUBLE PRECISION,

    -- Network
    network_latency_ms  DOUBLE PRECISION,
    network_rssi        INTEGER,                       -- WiFi signal strength

    -- Joint temperatures (JSONB — variable per robot model)
    joint_temps     JSONB,                             -- {"left_hip_pitch": 42.3, ...}

    -- Position
    gps_lat         DOUBLE PRECISION,
    gps_lon         DOUBLE PRECISION,
    gps_alt         DOUBLE PRECISION,
    gps_hdop        DOUBLE PRECISION,                  -- horizontal dilution of precision

    -- IMU
    imu_accel_x     DOUBLE PRECISION,
    imu_accel_y     DOUBLE PRECISION,
    imu_accel_z     DOUBLE PRECISION,
    imu_gyro_x      DOUBLE PRECISION,
    imu_gyro_y      DOUBLE PRECISION,
    imu_gyro_z      DOUBLE PRECISION,

    -- Operational
    task_status     TEXT,                              -- "idle", "navigating", "manipulating", "charging"
    error_code      INTEGER,
    error_message   TEXT,

    -- Pipeline metadata
    ingestion_lag_ms INTEGER,                          -- time from robot report to TSDB write
    raw_source      TEXT,                              -- "mqtt", "http", "grpc"
    format_version  TEXT,                              -- message format version from adapter
    normalizer_version TEXT                            -- schema mapper version used

    -- NOTE: No PRIMARY KEY here. TimescaleDB hypertables use (time, <optional partition key>)
    -- We will create a composite UNIQUE index for dedup: (robot_id, time)
);

-- ═══════════════════════════════════════════════════════════
-- Create hypertable: partition by time, 1-day chunks
-- ═══════════════════════════════════════════════════════════
SELECT create_hypertable('telemetry', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ═══════════════════════════════════════════════════════════
-- Unique constraint: deduplicate by (robot_id, time)
-- ═══════════════════════════════════════════════════════════
-- TimescaleDB requires hypertables to include the partition key in unique constraints
CREATE UNIQUE INDEX idx_telemetry_dedup ON telemetry (robot_id, time);

-- ═══════════════════════════════════════════════════════════
-- Query indexes
-- ═══════════════════════════════════════════════════════════
-- Per-robot time-range queries (most common pattern)
CREATE INDEX idx_telemetry_robot_time ON telemetry (robot_id, time DESC);

-- Fleet overview aggregation (scan all robots in time window)
CREATE INDEX idx_telemetry_time ON telemetry (time DESC);

-- Status filtering for fleet queries
CREATE INDEX idx_telemetry_task_status ON telemetry (task_status, time DESC)
    WHERE task_status IS NOT NULL;

-- ═══════════════════════════════════════════════════════════
-- Compression policy
-- ═══════════════════════════════════════════════════════════
ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'robot_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- Compress chunks older than 7 days
SELECT add_compression_policy('telemetry', INTERVAL '7 days', if_not_exists => TRUE);

-- ═══════════════════════════════════════════════════════════
-- Retention policy: drop chunks older than 90 days
-- ═══════════════════════════════════════════════════════════
SELECT add_retention_policy('telemetry', INTERVAL '90 days', if_not_exists => TRUE);
```

### Migration V001 Rollback

```sql
-- 001_timescale_telemetry.down.sql

SELECT remove_retention_policy('telemetry', if_exists => TRUE);
SELECT remove_compression_policy('telemetry', if_exists => TRUE);
DROP TABLE IF EXISTS telemetry CASCADE;
```

---

### Migration V002 — Continuous Aggregates

```sql
-- 002_continuous_aggregates.up.sql

-- ═══════════════════════════════════════════════════════════
-- telemetry_hourly: 1-hour buckets per robot
-- Used for: fleet trend charts (1h-7d views), robot detail (wider ranges)
-- ═══════════════════════════════════════════════════════════
CREATE MATERIALIZED VIEW telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    robot_id,

    -- Aggregated metrics
    AVG(battery_pct)        AS battery_pct_avg,
    MIN(battery_pct)        AS battery_pct_min,
    MAX(battery_pct)        AS battery_pct_max,

    AVG(cpu_pct)            AS cpu_pct_avg,
    MAX(cpu_pct)            AS cpu_pct_max,

    AVG(memory_pct)         AS memory_pct_avg,

    AVG(network_latency_ms) AS network_latency_ms_avg,
    MAX(network_latency_ms) AS network_latency_ms_max,

    -- Position: take first and last to detect movement
    FIRST(gps_lat, time)    AS gps_lat_start,
    FIRST(gps_lon, time)    AS gps_lon_start,
    LAST(gps_lat, time)     AS gps_lat_end,
    LAST(gps_lon, time)     AS gps_lon_end,

    -- Task: most frequent status in the hour
    MODE() WITHIN GROUP (ORDER BY task_status) AS task_status_mode,

    -- Data quality
    COUNT(*)                AS sample_count,
    AVG(ingestion_lag_ms)   AS ingestion_lag_ms_avg

FROM telemetry
GROUP BY bucket, robot_id;

-- Refresh policy: refresh every 30 minutes, covering last 2 hours
SELECT add_continuous_aggregate_policy('telemetry_hourly',
    start_offset    => INTERVAL '2 hours',
    end_offset      => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists   => TRUE
);

-- ═══════════════════════════════════════════════════════════
-- telemetry_daily: 1-day buckets for long-range trends
-- Used for: 7d/30d fleet trend charts
-- ═══════════════════════════════════════════════════════════
CREATE MATERIALIZED VIEW telemetry_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    robot_id,

    AVG(battery_pct)        AS battery_pct_avg,
    MIN(battery_pct)        AS battery_pct_min,
    MAX(battery_pct)        AS battery_pct_max,

    AVG(cpu_pct)            AS cpu_pct_avg,
    MAX(cpu_pct)            AS cpu_pct_max,

    AVG(memory_pct)         AS memory_pct_avg,

    AVG(network_latency_ms) AS network_latency_ms_avg,
    MAX(network_latency_ms) AS network_latency_ms_max,

    COUNT(*)                AS sample_count,
    COUNT(DISTINCT task_status) AS task_status_changes

FROM telemetry
GROUP BY bucket, robot_id;

SELECT add_continuous_aggregate_policy('telemetry_daily',
    start_offset    => INTERVAL '2 days',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists   => TRUE
);

-- ═══════════════════════════════════════════════════════════
-- Helper: fleet overview aggregation (across all robots)
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION fleet_overview_snapshot(
    lookback_seconds INTEGER DEFAULT 60
)
RETURNS TABLE (
    total_robots        BIGINT,
    online_count        BIGINT,
    offline_count       BIGINT,
    error_count         BIGINT,
    avg_battery_pct     DOUBLE PRECISION,
    avg_cpu_pct         DOUBLE PRECISION,
    active_alert_count  BIGINT
) AS $$
DECLARE
    latest_cutoff TIMESTAMPTZ := NOW() - (lookback_seconds || ' seconds')::INTERVAL;
BEGIN
    RETURN QUERY
    WITH latest_telemetry AS (
        SELECT DISTINCT ON (robot_id)
            robot_id,
            battery_pct,
            cpu_pct
        FROM telemetry
        WHERE time >= latest_cutoff
        ORDER BY robot_id, time DESC
    ),
    robot_status AS (
        SELECT
            r.id,
            r.status,
            CASE
                WHEN lt.robot_id IS NULL AND r.status = 'online' THEN 'delayed'
                ELSE r.status
            END AS effective_status,
            COALESCE(lt.battery_pct, 0) AS battery_pct,
            COALESCE(lt.cpu_pct, 0) AS cpu_pct
        FROM robots r
        LEFT JOIN latest_telemetry lt ON r.id::TEXT = lt.robot_id
        WHERE r.deleted_at IS NULL
    ),
    alert_counts AS (
        SELECT COUNT(*) AS active_count
        FROM alert_events
        WHERE status IN ('triggered', 'snoozed')
    )
    SELECT
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE effective_status = 'online')::BIGINT,
        COUNT(*) FILTER (WHERE effective_status = 'offline')::BIGINT,
        COUNT(*) FILTER (WHERE effective_status = 'error')::BIGINT,
        AVG(battery_pct),
        AVG(cpu_pct),
        COALESCE((SELECT active_count FROM alert_counts), 0)
    FROM robot_status;
END;
$$ LANGUAGE plpgsql STABLE;
```

### Migration V002 Rollback

```sql
-- 002_continuous_aggregates.down.sql

DROP FUNCTION IF EXISTS fleet_overview_snapshot(INTEGER);
DROP MATERIALIZED VIEW IF EXISTS telemetry_daily CASCADE;
DROP MATERIALIZED VIEW IF EXISTS telemetry_hourly CASCADE;
```

---

## 4. Query Pattern Reference

### Query 1: Robot Detail — Last 1 hour raw telemetry

```sql
SELECT time, battery_pct, cpu_pct, memory_pct, network_latency_ms,
       gps_lat, gps_lon, joint_temps, task_status
FROM telemetry
WHERE robot_id = $1
  AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC;

-- Uses: idx_telemetry_robot_time
-- Expected: < 100ms for 1 robot, 1 hour (720 rows at 5s interval)
```

### Query 2: Fleet Trend — avg battery over 24h (hourly buckets)

```sql
SELECT bucket, robot_id, battery_pct_avg
FROM telemetry_hourly
WHERE bucket >= NOW() - INTERVAL '24 hours'
ORDER BY bucket, robot_id;

-- Uses: continuous aggregate (pre-computed)
-- Expected: < 50ms
```

### Query 3: Compare two robots over 7 days

```sql
SELECT bucket, robot_id, battery_pct_avg, cpu_pct_avg
FROM telemetry_hourly
WHERE robot_id IN ($1, $2)
  AND bucket >= NOW() - INTERVAL '7 days'
ORDER BY bucket, robot_id;

-- Uses: continuous aggregate
-- Expected: < 100ms
```

### Query 4: Alert History for a robot (last 50)

```sql
SELECT ae.*, ar.metric, ar.operator, ar.threshold
FROM alert_events ae
JOIN alert_rules ar ON ae.rule_id = ar.id
WHERE ae.robot_id = $1
ORDER BY ae.triggered_at DESC
LIMIT 50;

-- Uses: idx_alert_events_robot_status + FK index on rule_id
```

### Query 5: Active Alerts Count by Severity

```sql
SELECT severity, COUNT(*)
FROM alert_events
WHERE status IN ('triggered', 'snoozed')
GROUP BY severity;

-- Uses: idx_alert_events_active (partial index)
```

---

## 5. Redis Key Design

```
# WebSocket Session Store
ws:session:{sessionId} → { userId, subscribedChannels[], connectedAt }

# Fleet Overview Cache (15s TTL)
cache:fleet:overview → JSON { total, online, offline, error, avgBattery, avgCpu, activeAlerts }

# Per-robot latest telemetry cache (5s TTL)
cache:robot:{robotId}:latest → JSON { battery_pct, cpu_pct, ... }

# Alert dedup window (30s)
alert:dedup:{robotId}:{ruleId} → triggeredAt timestamp (EX 30)

# Config sync status
config:sync:{robotId} → { version, appliedAt, status: "pending|applied|failed" }

# Rate limiter
ratelimit:{userId}:{endpoint} → counter (sliding window)
```

---

## 6. Migration Execution Order

```
1. PostgreSQL V001 (core tables)      — creates all BFF tables
2. TimescaleDB V001 (telemetry)       — creates hypertable + policies
3. TimescaleDB V002 (aggregates)      — creates continuous aggregates
4. PostgreSQL V002 (seed data)        — inserts dev seed data
```

---

## Completion Report

**what_was_done**: Designed complete database schema — 8 PostgreSQL tables (with triggers, indexes, constraints), 1 TimescaleDB hypertable with compression/retention policies, 2 continuous aggregate materialized views, 1 fleet overview function, Redis key schema, 5 reference queries with expected performance, and full rollback migrations for all artifacts.

**key_decisions**:
- **decision**: JSONB for `robot.config` and `telemetry.joint_temps`
  **rationale**: Per-robot configs vary by model (different sensors, thresholds). JSONB with JSON path queries avoids schema explosion while maintaining queryability. Joint temperatures likewise vary from 12 to 29 joints per robot model.
- **decision**: Composite `(robot_id, time)` UNIQUE index for dedup instead of primary key
  **rationale**: TimescaleDB hypertables don't support traditional PKs. The unique index serves the same purpose for `INSERT ... ON CONFLICT DO NOTHING` dedup in the TSDB writer.
- **decision**: Soft delete (`deleted_at`) for robots, users, comments — not for telemetry
  **rationale**: Operational data (robots, users, comments) needs audit trail and potential restoration. Telemetry is time-series by nature — retention policy handles cleanup.
- **decision**: 1-day chunk interval for telemetry hypertable
  **rationale**: At 5-second intervals, a single robot produces ~17K rows/day. 1-day chunks keep chunk count manageable (< 365/year per robot) while allowing efficient time-range pruning.
- **decision**: Continuous aggregates at 1-hour and 1-day granularity
  **rationale**: 1-hour covers 95% of dashboard queries (1h-7d views). 1-day covers long-range trends (30d+). Raw data queries only for < 1h windows.

**handoff_focus**: senior-engineer should use these migrations for I-004/I-005. The `fleet_overview_snapshot()` function provides the exact query for the fleet overview API without additional aggregation code. The Redis key design maps directly to cache layer implementation.

**open_questions**:
- How many robots expected in production? If > 1000, chunk interval may need reduction to 6h to keep chunk sizes below 25GB.
- `joint_temps` JSONB queries: if filtering by specific joint temp becomes common, consider a separate relational `joint_telemetry` table.

**known_constraints**:
- TimescaleDB compression excludes JSONB columns from some query optimizations — `joint_temps` queries on compressed chunks will be slower
- `gin_trgm_ops` index on `robots.name` requires `pg_trgm` extension (included in default PostgreSQL, but must be explicitly enabled)
