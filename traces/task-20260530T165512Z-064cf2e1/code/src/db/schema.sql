-- Robot Fleet Monitor — PostgreSQL Schema
-- Data retention: 30 days for telemetry, indefinite for config/metadata.

-- Robot metadata table (stable properties)
CREATE TABLE IF NOT EXISTS robots (
  robot_id      TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  protocol      TEXT NOT NULL,        -- e.g. 'json', 'protobuf', 'modbus'
  registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Time-series telemetry data (partitioned by day for fast drop)
CREATE TABLE IF NOT EXISTS telemetry (
  id              BIGSERIAL,
  robot_id        TEXT NOT NULL REFERENCES robots(robot_id),
  battery_level   REAL NOT NULL,
  joint_temperatures JSONB NOT NULL DEFAULT '{}',
  cpu_usage       REAL NOT NULL,
  network_latency REAL NOT NULL,
  task            TEXT NOT NULL DEFAULT '',
  latitude        REAL NOT NULL,
  longitude       REAL NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('online','offline','error','maintenance')),
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (robot_id, recorded_at)
);

-- Composite index for per-robot time-range queries
CREATE INDEX IF NOT EXISTS idx_telemetry_robot_time
  ON telemetry (robot_id, recorded_at DESC);

-- Index for recent data queries across all robots
CREATE INDEX IF NOT EXISTS idx_telemetry_time
  ON telemetry (recorded_at DESC);

-- Latest state cache is in Redis, but a DB fallback exists for full resets
-- (not a separate table; use ORDER BY recorded_at DESC LIMIT 1)

-- Alert rules configuration
CREATE TABLE IF NOT EXISTS alert_rules (
  id           SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  metric       TEXT NOT NULL,          -- e.g. 'battery_level', 'cpu_usage', 'status'
  operator     TEXT NOT NULL,          -- e.g. '<', '>', '==', '=='
  threshold    REAL,                   -- numeric threshold (NULL for status rules)
  target_value TEXT,                   -- status value to match (NULL for numeric rules)
  severity     TEXT NOT NULL DEFAULT 'warning',  -- 'info', 'warning', 'critical'
  enabled      BOOLEAN NOT NULL DEFAULT true,
  cooldown_s   INTEGER NOT NULL DEFAULT 300,    -- seconds before same alert re-fires
  escalate_after_s INTEGER DEFAULT NULL,        -- seconds before escalation
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Alert history
CREATE TABLE IF NOT EXISTS alerts (
  id          BIGSERIAL PRIMARY KEY,
  rule_id     INTEGER REFERENCES alert_rules(id),
  robot_id    TEXT NOT NULL REFERENCES robots(robot_id),
  metric      TEXT NOT NULL,
  value       TEXT NOT NULL,
  severity    TEXT NOT NULL,
  message     TEXT NOT NULL,
  acknowledged BOOLEAN NOT NULL DEFAULT false,
  fired_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_robot_time
  ON alerts (robot_id, fired_at DESC);

-- Global configuration key-value store
CREATE TABLE IF NOT EXISTS config (
  key        TEXT PRIMARY KEY,
  value      JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Collaboration messages (associated with robots)
CREATE TABLE IF NOT EXISTS messages (
  id          BIGSERIAL PRIMARY KEY,
  robot_id    TEXT REFERENCES robots(robot_id),
  user_name   TEXT NOT NULL,
  content     TEXT NOT NULL,
  mentions    TEXT[] NOT NULL DEFAULT '{}',
  handling    BOOLEAN NOT NULL DEFAULT false,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_robot_time
  ON messages (robot_id, created_at DESC);

-- Data retention: remove telemetry older than 30 days
CREATE OR REPLACE FUNCTION cleanup_old_telemetry() RETURNS void AS $$
BEGIN
  DELETE FROM telemetry WHERE recorded_at < now() - INTERVAL '30 days';
  DELETE FROM alerts WHERE fired_at < now() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
