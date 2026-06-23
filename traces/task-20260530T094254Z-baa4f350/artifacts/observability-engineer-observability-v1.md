# Observability Design: RoboEase Backend v3.0

## Summary

This document defines the observability strategy for the refactored RoboEase
backend services. It covers structured logging (PII-safe), in-process metrics
collection, correlation IDs for request tracing, health-check endpoints, and
alert threshold definitions. The implementation follows the quality criteria
from the observability-engineer harness: no PII in logs, structured context
over string interpolation, defined alert thresholds, and meaningful log levels.

---

## 1. Deliverables — Instrumented Files

### 1.1 New Files Created (6)

| File | Purpose |
|------|---------|
| `infrastructure/observability/__init__.py` | Package barrel exports |
| `infrastructure/observability/logging.py` | `structured_log()`, `mask_pii()`, `CorrelationIdFilter` |
| `infrastructure/observability/middleware.py` | `ObservabilityMiddleware` — correlation IDs + per-request logging + latency tracking |
| `infrastructure/observability/metrics.py` | `MetricsRegistry`, `REDMetrics`, `USEMetrics`, `get_metrics()` singleton |
| `infrastructure/observability/health.py` | `HealthCheck` registry, `/health`, `/health/detail`, `/metrics` endpoints |
| *This document* | `artifacts/observability-engineer-design-v1.md` |

### 1.2 Files Instrumented (6)

| File | What Changed |
|------|--------------|
| `services/agent_service.py` | 16 edits: structured_log for all CRUD, REDMetrics for Dify API calls, PII-safe error messages, request timeouts |
| `services/captchaService.py` | 4 edits: Fixed critical PII leak (SMTP password in `json.dumps(EMAIL_CONFIG)`), structured logging, captcha validation metrics |
| `services/userservice.py` | 4 edits: Login/signin metrics, user registration metrics, structured login success/failure logs (no PII) |
| `services/dictService.py` | 5 edits: Dict/item create/delete metrics + structured logs |
| `services/menuService.py` | 3 edits: Menu create/delete metrics + structured logs |
| `main.py` | 2 edits: Installed `ObservabilityMiddleware` and `/health` router |

---

## 2. What Is Observable

### 2.1 Correlation IDs (Request Tracing)

Every HTTP request receives or propagates a correlation ID
(`X-Correlation-Id` header). This ID is:

- **Injected into every log record** via `CorrelationIdFilter`
- **Returned in the response** header `X-Correlation-Id`
- **Logged in every request-summary** log entry with method, path, status, and latency

This allows tracing a single user action across all service calls and
correlating it with downstream MQTT messages, Dify API calls, and database
operations — even without a full distributed tracing backend.

### 2.2 HTTP Service Signals (RED Method)

Per-path metrics for **Rate, Errors, Duration**:

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests, labeled by path |
| `http_errors_total` | Counter | Failed requests (4xx/5xx), labeled by path and status code |
| `http_request_duration_ms` | Histogram | Per-request latency in milliseconds |

### 2.3 Domain Business Signals

| Metric Name | Type | Domain | Healthy | Unhealthy |
|-------------|------|--------|---------|-----------|
| `user_logins_total` | Counter (result=success\|failed) | Auth | >95% success rate | <80% success rate |
| `user_signins_total` | Counter (method, result) | Auth | email/mobile signup normal | account lookup failures spike |
| `user_registrations_total` | Counter | User | Steady rate | Zero for >24h (signup may be broken) |
| `agent_creates_total` | Counter | Agent | Steady rate | Zero for >24h |
| `agent_deletes_total` | Counter | Agent | Low rate | Spike may indicate bulk cleanup bug |
| `agent_installations_total` | Counter | Agent | Steady rate | Zero for >24h |
| `captcha_creates_total` | Counter | Captcha | Steady rate | Zero → captcha system down |
| `captcha_validations_total` | Counter (result) | Captcha | >90% success | >30% mismatch → brute-force attack |
| `emails_sent_total` | Counter | Email | >95% success (vs failed) | Failure rate >10% |
| `emails_failed_total` | Counter | Email | Near zero | Any steady increase |
| `dict_creates_total` | Counter | Dictionary | Steady | Zero for >24h |
| `dict_deletes_total` | Counter | Dictionary | Low | Spike |
| `dict_item_creates_total` | Counter | Dictionary | Steady | Zero for >24h |
| `dict_item_deletes_total` | Counter (count) | Dictionary | Low | Large bulk delete |
| `menu_creates_total` | Counter | Menu | Steady | Zero for >24h |
| `menu_deletes_total` | Counter | Menu | Low | Spike |

### 2.4 External Dependency Latency

| Signal | Source | Description |
|--------|--------|-------------|
| `agent_create` Dify API latency | `REDMetrics("agent_create")` in agent_service | Time to create a Dify app |
| Dify API HTTP status | Structured log context | 401/5xx logged per call |
| Database connectivity | `/health/detail` → `database: healthy/unhealthy` | Pool health via `pre_ping` |

### 2.5 Health-Check Endpoints

| Endpoint | Purpose | When Healthy | When Unhealthy |
|----------|---------|-------------|----------------|
| `GET /health` | Overall status | `{"status": "healthy"}` 200 | `{"status": "unhealthy"}` 503 |
| `GET /health/detail` | Dependency + metrics | All dependencies healthy | Any critical dependency unhealthy |
| `GET /metrics` | Raw metrics snapshot | N/A | N/A (data endpoint) |

**Dependency checks registered by default:**
- `database` (critical) — `SELECT 1` via SQLAlchemy engine
- `api` (critical) — always healthy when reachable

**Extend with Redis/MQTT/Dify later:**
```python
from infrastructure.observability.health import HealthCheck
health = HealthCheck()
health.register("redis", check_redis_fn, critical=False)
health.register("mqtt", check_mqtt_fn, critical=False)
health.register("dify_api", check_dify_fn, critical=False)
```

---

## 3. Alert Thresholds

### 3.1 Critical Alerts

| Alert | Threshold | Window | Severity | Runbook |
|-------|-----------|--------|----------|---------|
| **High HTTP 5xx Rate** | >5% of requests | 5 min | CRITICAL | Check logs for exception traces, DB connectivity, Dify API status |
| **Database Unhealthy** | `/health` reports unhealthy | Immediate | CRITICAL | Check DB connection string, pool exhaustion, network |
| **Login Failure Spike** | `user_logins_total{failed}` > 10/min | 5 min | CRITICAL | Possible brute-force attack or auth bug. Check `captcha_validations_total` for bypass |

### 3.2 Warning Alerts

| Alert | Threshold | Window | Severity | Runbook |
|-------|-----------|--------|----------|---------|
| **High HTTP 4xx Rate** | >10% of requests | 5 min | WARNING | Check for client-side errors, invalid tokens, API version mismatch |
| **P95 Latency > 1s** | `http_request_duration_ms` p95 > 1000ms | 5 min | WARNING | Check DB slow queries, Dify API latency, GC pauses |
| **Email Failure Rate** | `emails_failed_total` / `emails_sent_total` > 0.05 | 15 min | WARNING | SMTP server may be down or credentials expired |
| **Captcha Validation Mismatch > 30%** | `captcha_validations_total{mismatch}` / total > 0.3 | 5 min | WARNING | Possible bot attack or captcha display bug |
| **Zero Agent Creates in 24h** | `agent_creates_total` delta = 0 over 24h | 24h | WARNING | Agent creation flow may be broken (check Dify API availability) |

### 3.3 Non-Alert Signals (Informational)

The following are collected for dashboards but do NOT generate alerts:

- `dict_*` counters — dictionaries are infrequently modified
- `menu_*` counters — menus are infrequently modified
- Individual HTTP request latencies below p95
- `agent_installations_total` — dependent on marketplace activity

**Reason for non-alerting:** These signals have no operational urgency.
They are valuable for trend analysis but would generate false positives if
alerted on.

---

## 4. Log Level Standards

| Level | When to Use | Example |
|-------|------------|---------|
| **DEBUG** | Internal state useful for local development. Not enabled in production. | `structured_log("DEBUG", "Looking up installed agent key", dify_agent_id=...)` |
| **INFO** | Operational signal — a meaningful business event occurred. | `structured_log("INFO", "User login succeeded", entity="User", user_id=...)` |
| **WARNING** | Recoverable anomaly — something unexpected but the system handled it. | `structured_log("WARNING", "User login failed", method="password")` |
| **ERROR** | Requires human attention — external call failed, data corruption, unhandled path. | `structured_log("ERROR", "Dify API returned 401 creating app", http_status=401)` |

---

## 5. PII Remediation

### 5.1 Fixed in This Iteration

| File | Issue | Fix |
|------|-------|-----|
| `captchaService.py:send_email` | Logged full SMTP config including `sender_password` via `json.dumps(EMAIL_CONFIG)` | Replaced with structured log showing `smtp_server`, `smtp_port`, `sender_email`, but NOT `sender_password` |
| `agent_service.py` multiple | Logged Dify API responses containing tokens and internal IDs | Replaced with `structured_log` showing only `http_status`, business fields (no raw responses) |
| `userservice.py:login` | `logger.info(f"登录请求: username={loginRequest.username}")` leaked username | Replaced with `structured_log("INFO", "User login succeeded", user_id=..., method="password")` — logs user_id (internal) not username |

### 5.2 Built-in PII Protection

The `structured_log()` function in `logging.py` automatically masks:
- Email addresses → `***@***`
- Phone numbers → `138****1234` pattern
- JWT tokens → `[JWT-REDACTED]`
- Known sensitive keys (password, token, secret, api_key, etc.) → `[REDACTED]`

This is applied by default (`pii_safe=True`).

---

## 6. Healthy vs Unhealthy Signals

### 6.1 Healthy System

```
GET /health → 200 {"status": "healthy"}
GET /health/detail → All dependencies "healthy"

http_requests_total:     Steadily increasing
http_errors_total:       < 1% of requests
http_request_duration_ms: p95 < 500ms
user_logins_total{failed}: Near zero
emails_failed_total:     Near zero
captcha_validations_total{mismatch}: < 10%
```

### 6.2 Degraded System

```
GET /health → 200 {"status": "degraded"}   (non-critical dep down, e.g. Redis)
GET /health/detail → One non-critical dep "unhealthy"

http_request_duration_ms: p95 > 1s (but < 5s)
emails_failed_total:      Increasing above 5% rate
```

### 6.3 Unhealthy System

```
GET /health → 503 {"status": "unhealthy"}   (database down, API unreachable)
http_errors_total:     > 5% of requests (sustained)
user_logins_total{failed}: > 10/min sustained
captcha_validations_total{mismatch}: > 30% sustained (probable attack)
```

---

## 7. Integration With Existing Infrastructure

### 7.1 Compatibility

- **loguru** continues as the primary logging framework
- **log_setting.py** custom format continues to work; the `structured_log()` helper wraps `logger.bind(**context).log()`
- **Exception handlers** in `core/exception_handlers.py` still fire (observability middleware is a separate layer)
- **MQTT client** in `common/mqtt_client.py` is not affected

### 7.2 Prometheus/Grafana Readiness

The `GET /metrics` endpoint returns a JSON snapshot mirroring Prometheus format.
When Prometheus is available, a scraper can consume this directly or the
counters can be pushed via push-gateway.

### 7.3 Future: Distributed Tracing

The correlation ID infrastructure (`X-Correlation-Id` header propagation)
is the foundation for full distributed tracing with OpenTelemetry or Jaeger.

---

## 8. Technical Debt Documented

| Item | Risk | Mitigation |
|------|------|------------|
| `synergy_service.py` (10 direct Session calls) | Medium | Not yet instrumented; would benefit from REDMetrics |
| `device_service.py` (8 direct Session calls) | Medium | Not yet instrumented; existing log statements need PII review |
| `userservice.py` FIXME (2 direct Session calls) | High | Login/signin still uses `Session(engine)` directly |
| No Redis/MQTT health checks yet | Low | Dependencies not instrumented; add via HealthCheck.register() |
| Dify API calls lack circuit breaker | Medium | Repeated 401/5xx responses will trigger per-call ERROR logs but no backoff |