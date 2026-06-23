# Data Design: RoboEase Refactor — Database Schema & Migration Strategy v3

## 1. Source Evidence & Scope

### 1.1 Confirmed Facts (Workspace-Verified)

| Evidence | Source | Finding |
|----------|--------|---------|
| Database engine | `docker/edge/docker-compose.yaml` L97 | **MySQL 8.0** with `utf8mb4_general_ci` |
| Backend framework | `docker/edge/docker-compose.yaml` L69 | FastAPI (Python) via `DATABASE_URL=mysql+pymysql://...` |
| ORM layer | Cannot verify — backend source absent | Assumed SQLAlchemy 2.0+ / SQLModel |
| MQTT broker | `docker/edge/docker-compose.yaml` L122 | EMQX 5.8.4 |
| Admin mock API | `frontend/admin/mock/*.mock.ts` | 10+ mock files, numeric result codes (200) |
| Portal mock API | `frontend/portal/src/api/auth.api.ts` | `/api/v1/auth`, string result codes (`"00000"`) |
| Shared package | `frontend/shared/src/` (v1 implementation) | HTTP client, auth API, token storage factories |
| Robot heartbeat | Inferred from robot mock + API | Serial-number based identification, per-second polling likely |

### 1.2 What We Cannot Verify (Backend Source Missing)

- Actual SQLAlchemy/SQLModel entity definitions
- Existing schema DDL (no `dbscripts/` in workspace)
- Existing production data volumes
- Snowflake ID generator configuration (if any)
- Current index and FK state
- Whether `enterprise_id` is applied to ALL tables or only some

### 1.3 Entity Inventory (Derived from Frontend API + Mock Data)

The following 33 entities are derived from admin mock data and API type definitions:

| # | Entity | Mock Evidence | API File |
|---|--------|--------------|----------|
| 1 | `user` | `user.mock.ts` — `user/page`, `users/:id/form`, `user/me` | `user.api.ts` |
| 2 | `sys_enterprise` | Implied by `enterprise_id` FK pattern across all mock data | — (multi-tenant infra) |
| 3 | `sys_role` | `role.mock.ts` — `roles/page`, `roles/:id/form` | Implied |
| 4 | `sys_menu` | `menu.mock.ts` — `menus`, `menus/routes`, `menus/:id/form` | Implied |
| 5 | `sys_dept` | `dept.mock.ts` — `dept`, `dept/options`, `dept/:id/form` | Implied |
| 6 | `sys_user_role` | `user.mock.ts` — `roleIds: [2]` on user objects | Junction |
| 7 | `sys_role_menu` | `role.mock.ts` — `roles/:id/menuIds`, `roles/:id/menus` | Junction |
| 8 | `sys_user_enterprise` | Multi-tenant pattern — user↔enterprise scoping | Junction |
| 9 | `robot` | `robot.mock.ts` — `robot/page`, `robot/:id/form` | `robot.api.ts` |
| 10 | `robot_ext_info` | `robotext.api.ts` — `/robot/ext-info/*` CRUD endpoints | `robotext.api.ts` |
| 11 | `dict` | `dict.mock.ts` — `dicts`, `dicts/page` | Implied |
| 12 | `dict_item` | `dict.mock.ts` — `dicts/:dictCode/items`, `dicts/:dictCode/items/page` | Implied |
| 13 | `sys_config` | `user.mock.ts` — `sys:config:*` perms | Implied |
| 14 | `notice` | `notice.mock.ts` — `notices/page`, `notices/:id/form`, `notices/my-page` | Implied |
| 15 | `notice_user_read` | Implied by `isRead` field on notice mock items | Junction |
| 16 | `task_info` | `task.api.ts` — `/task/page`, `/task/detail/:id`, `/task/create` | `task.api.ts` |
| 17 | `task_info_detail` | `task.api.ts` — `TaskDetail.details[]` with step data | `task.api.ts` |
| 18 | `task_result_detail` | `task.api.ts` — `/task/result/:id`, `/task/save_result` | `task.api.ts` |
| 19 | `dashboard` | `dashboard.api.ts` — `/dashboard/stats` | `dashboard.api.ts` |
| 20 | `agent_info` | `agent.api.ts` — `/agent/keys` | `agent.api.ts` |
| 21 | `recommended_agent_info` | Implied — agent template library in portal mock | Implied |
| 22 | `action_library_info` | Implied — task composition involves motions | Implied |
| 23 | `expression_library_info` | Implied — task composition involves emotions | Implied |
| 24 | `voice_library_info` | Implied — task TTS operations | Implied |
| 25 | `knowledge_library_info` | Implied — agent knowledge base | Implied |
| 26 | `screen_project` | `screenproject.api.ts` — `/screenproject/*` CRUD | `screenproject.api.ts` |
| 27 | `screen_page` | `screenproject.api.ts` — `/screenproject/page/*` | `screenproject.api.ts` |
| 28 | `screen_robot_log` | Implied — screen project robot communication log | Implied |
| 29 | `synergy_info` | `synergy.api.ts` — `/synergy/*` CRUD | `synergy.api.ts` |
| 30 | `synergy2_info` | `synergy2.api.ts` — `/synergy2/*`, `/scenes/*`, `/resources/*` | `synergy2.api.ts` |
| 31 | `device` | Implied — robot management domain | Implied |
| 32 | `log_extract_result` | `extractLogs.api.ts` — `/extractLogs/*` | `extractLogs.api.ts` |
| 33 | `captcha` | `auth.mock.ts` — `auth/captcha` | `auth.api.ts` |

---

## 2. Design Principles

1. **MySQL 8.0 is the sole target** — confirmed by docker-compose. Use InnoDB, `utf8mb4_0900_ai_ci`, JSON type, CHECK constraints, CTEs, window functions, online DDL.
2. **Normalization by default** — every column has a reason; denormalization documented explicitly.
3. **FK constraints mandatory** — `ON DELETE RESTRICT` for operational safety; `CASCADE` only for junction tables.
4. **Nullable only with documented reason** — every nullable column has a comment explaining why.
5. **Indexes reference specific query patterns** — no "intuition indexes."
6. **Up + down migrations always paired** — rollback written before forward ships.
7. **Zero-downtime for production** — expand-contract pattern; no table-locking DDL without stated strategy.
8. **Naming convention**: `lowercase_snake_case`, singular table names, `_at` suffix for timestamps, `_by` for audit user IDs.
9. **Soft-delete via `deleted_at` DATETIME(3) NULL** — NULL=active; timestamp enables TTL cleanup.
10. **ID type**: `BIGINT AUTO_INCREMENT` — MySQL-optimal.

---

## 3. Entity-Relationship Map

```
sys_enterprise ──1:N── user (via sys_user_enterprise junction)
sys_enterprise ──1:N── sys_role
sys_enterprise ──1:N── robot
sys_enterprise ──1:N── task_info
sys_enterprise ──1:N── agent_info
sys_enterprise ──1:N── action_library_info
sys_enterprise ──1:N── expression_library_info
sys_enterprise ──1:N── voice_library_info
sys_enterprise ──1:N── knowledge_library_info
sys_enterprise ──1:N── synergy_info
sys_enterprise ──1:N── synergy2_info
sys_enterprise ──1:N── device

sys_dept ──1:N── user
sys_dept (self-referential: parent_id → id)

user ──N:M── sys_role (via sys_user_role)
user ──N:M── sys_enterprise (via sys_user_enterprise)
sys_role ──N:M── sys_menu (via sys_role_menu)

robot ──1:N── robot_ext_info
robot ──1:N── task_info

task_info ──1:N── task_info_detail
task_info ──1:N── task_result_detail
task_info ──1:N── log_extract_result

notice ──1:N── notice_user_read
notice_user_read ──N:1── user

screen_project ──1:N── screen_page
screen_project ──1:N── screen_robot_log

dict ──1:N── dict_item (logical, via dict_code)
```

---

## 4. Migration Files

### 4.1 Migration Infrastructure

Migrations are raw SQL files targeting MySQL 8.0 under `backend/migrations/`:

```
backend/migrations/
├── runner.py                          # Zero-dependency migration runner
├── 001_baseline_schema.up.sql
├── 001_baseline_schema.down.sql
├── 002_add_fk_constraints.up.sql
├── 002_add_fk_constraints.down.sql
├── 003_add_query_indexes.up.sql
├── 003_add_query_indexes.down.sql
├── 004_add_audit_triggers.up.sql
├── 004_add_audit_triggers.down.sql
├── 005_add_check_constraints.up.sql
├── 005_add_check_constraints.down.sql
├── 006_seed_rbac_data.up.sql
└── 006_seed_rbac_data.down.sql
```

### 4.2 Migration Runner

The runner is a zero-dependency Python script that tracks applied migrations in a `__migrations` table with checksum support. It reads `DATABASE_URL` from environment and supports `python runner.py up|down`.

---

## 5-13. [Full Schema Design, Migrations, Indexes, Triggers, CHECK Constraints, Seed Data, EXPLAIN Analysis, Retention, ORM Mapping]

See the complete artifact at `/Users/ZQ/roboease/artifacts/database-engineer-data-design-v3.md` for:
- 30 CREATE TABLE DDL statements with column comments and nullable justifications
- 6 sequential migration files (up.sql + down.sql pairs)
- 24 index justifications referencing specific frontend query patterns
- 5 EXPLAIN plan analyses for critical queries (task listing, robot heartbeat, user login, permission check, unread count)
- Retention/cleanup policies with MySQL Event Scheduler
- SQLAlchemy/SQLModel ORM mapping guidance
- Column rename reference table for backward compatibility
- Migration execution strategy with rollback procedures

---

## 14. Completion Report

```yaml
completion_report:
  what_was_done: |
    Designed a comprehensive, production-ready database schema for the RoboEase
    platform targeting MySQL 8.0. Created 30 table definitions with full foreign
    key constraints, query-pattern-referenced indexes, CHECK constraints, audit
    triggers, and a complete migration strategy (6 sequential migrations, each
    with up.sql and down.sql).

    Key deliverables beyond v2:
    - Zero-dependency Python migration runner (runner.py) with __migrations tracking
    - CHECK constraints migration (005) for domain integrity at DB level
    - RBAC seed data migration (006) for minimum viable setup
    - Expanded task_info status from 2 to 6 values based on task.api.ts endpoints
    - Added screen_project voice-interaction fields (start_word, interrupt_word, continue_word)
    - Improved EXPLAIN analysis with expected row estimates
    - SQLAlchemy/SQLModel ORM mapping guidance for downstream engineers
    - Explicit robot password encryption strategy (AES-256-GCM, application-layer)

  key_decisions:
    - decision: MySQL 8.0 is the sole target database
      rationale: Confirmed by docker-compose. The codebase includes pymysql driver.
    - decision: BIGINT AUTO_INCREMENT as primary key type
      rationale: MySQL-optimal. 8 bytes vs 20+ for VARCHAR.
    - decision: Separate migrations into 6 sequential files
      rationale: Enables targeted rollback and independent testing.
    - decision: ON DELETE RESTRICT for operational entities, CASCADE for junctions
      rationale: Preserve task history on robot delete; cascade clean junctions.
    - decision: Application-layer password encryption; DB stores ciphertext only
      rationale: Even if DB compromised, robot credentials stay protected.
    - decision: Soft-delete via deleted_at DATETIME(3) instead of boolean
      rationale: Enables TTL-based hard-delete cleanup and audit trail.
    - decision: Zero-dependency Python migration runner over Alembic
      rationale: Simpler for <10 dev team; Alembic can be adopted later.

  handoff_focus:
    - senior-engineer: Implement SQLModel entities, repository base class, wire migration runner
    - api-designer: Update OpenAPI docs for renamed fields
    - devops-engineer: Configure my.cnf, enable Event Scheduler, set up backups
    - performance-engineer: Validate indexes against production slow query log

  open_questions:
    - What is the actual row count per table in production?
    - What is the robot heartbeat frequency?
    - Does the existing schema use BIGINT or VARCHAR(20) for PKs?
    - Is enterprise_id applied to ALL tables in production?
    - What ORM is actually used?
    - What is the data volume for task_result_detail?

  known_constraints:
    - Backend source code is absent; schema inferred from frontend API + mock data
    - MySQL 8.0 confirmed by docker-compose; actual deployment may vary
    - Team size <10 developers; migration complexity must be manageable
    - Production data volume unknown

  confidence_differential: 0.70
  dissent_if_alone: null
  iteration_context: v3 refines v2 with production-ready runner, CHECK constraints, seed data, improved EXPLAIN analysis, and ORM mapping guidance.
```
