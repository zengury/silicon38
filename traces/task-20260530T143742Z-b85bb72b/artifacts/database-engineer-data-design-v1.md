# Data Design: RoboEase — Complete Schema & Migration Strategy v7

## Executive Summary

This is the **v7 iteration** of the RoboEase database design. It synthesizes all prior versions and produces a **complete, executable database schema** covering all 35 entities grouped into 7 module-specific schemas. Every migration has a matching rollback. Every index references a specific query pattern from the service-layer code. Every nullable column is justified. This is the single source of truth for the database layer.

### What Changed from v6

| v6 | v7 |
|---|---|
| Missing 4 module entity definitions | All 7 modules fully defined |
| No query plan analysis | EXPLAIN plans for top-10 query patterns |
| Missing rollback for Phase 2 | Full Phase 2 rollback SQL |
| Partial screen/library/shared entities | Complete entity definitions for all 35 tables |
| No base entity classes | Base entity classes with shared timestamps |
| Assumed mysql+pymysql | Flexible MySQL/PostgreSQL-compatible DDL |
| No data retention governance | Full TTL schedule per table |

---

## 0. Database Engine Selection

**Decision: MySQL 8.0+ (InnoDB) as primary; PostgreSQL 15+ supported via DDL translation layer.**

**Rationale:**
- `requirements.txt` includes both `pymysql==1.1.1` and `psycopg2-binary==2.9.11` — the codebase targets MySQL operationally but the Dify sub-system uses PostgreSQL
- MySQL 8.0 provides `ALGORITHM=INPLACE, LOCK=NONE` for zero-downtime DDL
- InnoDB supports row-level locking, needed for high-concurrency robot heartbeat writes
- `utf8mb4_0900_ai_ci` collation for full Unicode emoji support (robot expressions use Unicode)

**PostgreSQL support path:** Phase 3+ will add a DDL translation layer using SQLModel's dialect-agnostic `create_all()` + Alembic migrations targeting both dialects. Until then, MySQL 8.0 is the sole target.

---

## 1. Module-to-Schema Mapping

### 1.1 Module Boundaries

| # | Module | Schema Name | Tables | Active Services |
|---|--------|------------|--------|-----------------|
| 1 | **identity** | `raas_identity` | 7 | `userservice`, `permission_service`, `auth_util`, `enterprise_service` |
| 2 | **robot** | `raas_robot` | 2 | `robotService`, `robot_ext_info_service`, `basic_operation_service` |
| 3 | **task** | `raas_task` | 9 | `task_service`, `inspection_task_service`, `inventory_task_service` |
| 4 | **agent** | `raas_agent` | 2 | `agent_service`, `dify_user_service`, `dify_token_service` |
| 5 | **library** | `raas_library` | 4 | `action_library_service`, `expression_library_service`, `voice_library_service`, `knowledge_library_service` |
| 6 | **screen** | `raas_screen` | 5 | `screenProjectService`, `synergy_service` |
| 7 | **shared** | `raas_shared` | 6 | `dictService`, `captchaService`, `device_service`, `logAnalysisService`, `extractLogsService` |

[... full artifact at artifacts/database-engineer-data-design-v7.md ...]