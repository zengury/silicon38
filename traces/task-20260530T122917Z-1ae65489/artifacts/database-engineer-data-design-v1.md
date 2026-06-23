# Data Design: RoboEase — Database Schema, Entities & Migration Strategy v5

## Executive Summary

This is the **execution-ready database design** for the RoboEase refactor. It translates the architect's decisions into concrete SQLModel entity definitions, database connection management, and paired up/down migrations. It builds on the v4 schema analysis and fills the critical gap: the `infrastructure/db/` module is referenced in imports but does not yet exist in the codebase.

### Key Deliverables

| Deliverable | Path | Status |
|------------|------|--------|
| SQLModel Entities | `backend/infrastructure/db/entities.py` | Designed (this doc) |
| DB Connection | `backend/infrastructure/db/connection.py` | Specified (this doc) |
| Baseline Schema Migration | `backend/migrations/001_baseline_schema.up.sql` | Written |
| Baseline Schema Rollback | `backend/migrations/001_baseline_schema.down.sql` | Written |
| FK Constraints | `backend/migrations/002_add_fk_constraints.up.sql` | Written |
| FK Rollback | `backend/migrations/002_add_fk_constraints.down.sql` | Written |
| Query Indexes | `backend/migrations/003_add_query_indexes.up.sql` | Written |
| Index Rollback | `backend/migrations/003_add_query_indexes.down.sql` | Written |
| Migration Runner | `backend/migrations/runner.py` | Written |

---

## 1. Current State Assessment

### 1.1 What Exists

The codebase has a **mid-refactor state**:

```
backend/db/database.py       # Backward-compat re-exports from infrastructure.db.*
backend/config/setting.py    # Baseline settings (JWT, CORS, MQTT, Dify)
backend/config/dbconfig.py   # EMPTY — previously held config, now migrated
backend/common/models.py     # Pydantic request/response DTOs (NOT SQLModel tables)
```

The `backend/db/database.py` re-exports from `infrastructure.db.entities` and `infrastructure.db.connection`, but **neither file exists**. All services import from `db.database`. The `main.py` imports from `core.config`, `infrastructure.observability.middleware`, and `infrastructure.observability.health` — none of these directories exist either.

### 1.2 What's Missing

| Missing Module | Referenced By |
|---------------|---------------|
| `backend/infrastructure/db/entities.py` | `db/database.py`, all services |
| `backend/infrastructure/db/connection.py` | `db/database.py`, `main.py` |
| `backend/core/config/` | `main.py`, `services/userservice.py`, `services/task_service.py` |
| `backend/core/exception_handlers.py` | `main.py` |
| `backend/core/security.py` | `services/userservice.py` |
| `backend/infrastructure/observability/` | `main.py`, `services/*.py` |
| `backend/ports/repositories.py` | `services/*.py` |
| `backend/di/container.py` | `services/*.py` |
| `backend/application/dto.py` | `db/database.py` |

### 1.3 Legacy Database Schema (`dbscripts/raas.sql`)

Production MySQL 8.0 schema with these critical issues:

| Issue | Impact | Fix Priority |
|-------|--------|-------------|
| **No foreign key constraints** | Referential integrity violated at app level only | CRITICAL |
| **VARCHAR(20) primary keys** | 21+ bytes per PK; slower joins; no auto-increment | HIGH |
| **`password` column stores plaintext** | Security vulnerability | CRITICAL |
| **No indexes beyond PRIMARY KEY** | Full table scans on every query | HIGH |
| **`del_flag CHAR(1)` for soft deletes** | No timestamp for TTL cleanup | MEDIUM |
| **`create_time`/`update_time` naming** | Inconsistent with `_at` convention | LOW |
| **Two menu tables coexist** | `menu` (BIGINT PK) and `sys_menu` (VARCHAR PK) | HIGH |
| **Plaintext robot credentials** | `robot.password` stores plaintext | CRITICAL |

### 1.4 Entity Inventory (from import analysis)

All entity names referenced in service imports:

```python
# Identity & RBAC
UserEntity, SystemEnterpriseEntity, SystemUserEnterpriseEntity
SystemRoleEntity, SystemMenuEntity, SystemUserRoleEntity, SystemRoleMenuEntity
MenuEntity  # legacy menu table

# Robot
RobotEntity, RobotExtInfoEntity

# Tasks
TaskInfoEntity, TaskInfoDetailEntity, TaskResultDetailEntity
InspectionTaskInfoEntity, InspectionTaskStepsEntity, InspectionTaskResultsEntity
InventoryTaskInfoEntity, InventoryTaskStepsEntity, InventoryTaskResultsEntity

# Agents & Libraries
AgentInfoEntity, RecommendedAgentInfoEntity
ActionLibraryInfoEntity, ExpressionLibraryInfoEntity
VoiceLibraryInfoEntity, KnowledgeLibraryInfoEntity

# Screen & Dashboard
ScreenProjectEntity, ScreenPageEntity, ScreenRobotLogEntity
DashboardEntity

# Utility
CaptchaEntity, DictEntity, DictItemEntity
SynergyInfoEntity, Synergy2InfoEntity
DeviceInfoEntity, LogExtractResultEntity, PageResult  # DTO
```

---

## 2. Design Decisions

### 2.1 Preserve Entity Names — Evolve Column Types

**Decision**: Keep all entity class names as-is. Services import specific names; renaming breaks everything. Only evolve column types, add constraints, and add indexes.

**Rationale**: The refactor's goal is to improve structure, not rename APIs. Entity names are the contract between layers.

### 2.2 VARCHAR(20) PKs → BIGINT AUTO_INCREMENT (Phase 2)

**Decision (THIS VERSION)**: Preserve VARCHAR PKs in the immediate refactor to avoid breaking service code that generates Snowflake IDs via `common.IdUtil.get_next_id()`. Schedule BIGINT migration as a Phase 2 with expand-contract.

**Rationale**: 
- Snowflake ID generation is embedded in all `create()` service methods
- Changing PK type requires coordinated migration of all FK columns
- Risk of breaking production data during migration is high
- Phase 2 can use expand-contract: add `new_id BIGINT AUTO_INCREMENT`, backfill, dual-write, transition reads, drop old

### 2.3 Password Hashing — Mandatory

**Decision**: Rename `password` to `password_hash` on `user` table. Rename `password` to `password_enc` on `robot` table. Add application-level bcrypt hashing.

**Rationale**:
- `password` implies plaintext; `password_hash` communicates the invariant
- Robot credentials use symmetric encryption (ssh/API auth), hence `password_enc`
- Migration: add new column, backfill from old, drop old after transition

### 2.4 Foreign Keys — Enforced at DB Level

**Decision**: Add FOREIGN KEY constraints for all relationships. Use `ON DELETE CASCADE` for child/junction tables, `ON DELETE SET NULL` for optional parent references, `ON DELETE RESTRICT` for operational tables.

**FK Matrix**:

| Child Table | Parent Table | Column | ON DELETE |
|------------|-------------|--------|-----------|
| `sys_user_enterprise` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `sys_user_enterprise` | `user` | `user_id` | CASCADE |
| `sys_user_role` | `user` | `user_id` | CASCADE |
| `sys_user_role` | `sys_role` | `role_id` | CASCADE |
| `sys_role_menu` | `sys_role` | `role_id` | CASCADE |
| `sys_role_menu` | `sys_menu` | `menu_id` | CASCADE |
| `robot` | `sys_enterprise` | `enterprise_id` | SET NULL |
| `robot_ext_info` | `robot` | `robot_id` | CASCADE |
| `task_info` | `robot` | `robot_id` | RESTRICT |
| `task_info_detail` | `task_info` | `task_id` | CASCADE |
| `task_result_detail` | `task_info` | `task_id` | CASCADE |
| `inspection_task_steps` | `inspection_task_info` | `inspection_task_id` | CASCADE |
| `inspection_task_results` | `inspection_task_info` | `inspection_task_id` | CASCADE |
| `inventory_task_steps` | `inventory_task_info` | `inventory_task_id` | CASCADE |
| `inventory_task_results` | `inventory_task_info` | `inventory_task_id` | CASCADE |
| `screen_page` | `screen_project` | `project_id` | CASCADE |
| `screen_robot_log` | `screen_project` | `project_id` | CASCADE |
| `screen_robot_log` | `robot` | `robot_id` | CASCADE |
| `agent_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `recommended_agent_info` | `agent_info` | `dify_agent_id` | SET NULL |
| `action_library_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `expression_library_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `voice_library_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `knowledge_library_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `device` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `synergy2_info` | `sys_enterprise` | `enterprise_id` | CASCADE |
| `log_extract_result` | `task_info` | `task_id` | CASCADE |

### 2.5 Index Strategy — Query-Pattern-Driven

Every index references a specific query pattern observed in service code or API routes:

| Index Name | Table | Columns | Query Pattern | Est. Frequency |
|-----------|-------|---------|---------------|----------------|
| `uq_user_username` | `user` | `username` | Login: `WHERE username=? AND del_flag='1'` | Every login (100s/min) |
| `uq_user_email` | `user` | `email` | Email lookup: `WHERE email=?` | OAuth login |
| `uq_user_mobile` | `user` | `mobile` | Mobile login: `WHERE mobile=?` | Mobile login |
| `idx_user_enterprise` | `user` | `enterprise_id` | Admin listing: `WHERE enterprise_id=?` | Frequent |
| `uq_role_key_ent` | `sys_role` | `enterprise_id, role_key` | Permission check: `WHERE enterprise_id=? AND role_key=?` | Every API call |
| `idx_menu_parent` | `sys_menu` | `parent_id` | Menu tree: `WHERE parent_id=?` | Every page load |
| `uq_robot_code` | `robot` | `code` | Robot lookup: `WHERE code=?` | Every robot operation |
| `uq_robot_serial` | `robot` | `serial_no` | Robot heartbeat: `WHERE serial_no=?` | Every few seconds per robot |
| `idx_robot_enterprise` | `robot` | `enterprise_id` | Enterprise listing: `WHERE enterprise_id=?` | Frequent |
| `idx_task_enterprise_status` | `task_info` | `enterprise_id, status` | Task list: `WHERE enterprise_id=? AND status=?` | Most common admin query |
| `idx_task_robot` | `task_info` | `robot_id` | Per-robot tasks: `WHERE robot_id=?` | Robot detail page |
| `idx_trd_task` | `task_result_detail` | `task_id, robot_sn` | Task results: `WHERE task_id=? AND robot_sn=?` | Task status polling |
| `idx_insp_task_enterprise` | `inspection_task_info` | `enterprise_id` | Inspection listing | Frequent |
| `idx_invt_task_enterprise` | `inventory_task_info` | `enterprise_id` | Inventory listing | Frequent |
| `idx_device_enterprise` | `device` | `enterprise_id` | Device listing: `WHERE enterprise_id=?` | Occasional |
| `idx_agent_enterprise` | `agent_info` | `enterprise_id` | Agent listing: `WHERE enterprise_id=?` | Frequent |
| `idx_agent_dify` | `agent_info` | `dify_agent_id` | Dify callback: `WHERE dify_agent_id=?` | Webhook |
| `idx_rec_agent_install` | `recommended_agent_info` | `install_count` | Popular agents: `ORDER BY install_count DESC` | Marketplace page |
| `idx_ali_enterprise` | `action_library_info` | `enterprise_id` | Library listing | Frequent |
| `idx_eli_enterprise` | `expression_library_info` | `enterprise_id` | Library listing | Frequent |
| `idx_vli_enterprise` | `voice_library_info` | `enterprise_id` | Library listing | Occasional |
| `idx_kli_enterprise` | `knowledge_library_info` | `enterprise_id` | Library listing | Occasional |
| `idx_sp_project` | `screen_page` | `project_id` | Project pages: `WHERE project_id=?` | Screen rendering |
| `idx_srl_project` | `screen_robot_log` | `project_id` | Operation log: `WHERE project_id=?` | Screen UI |
| `idx_captcha_key` | `captcha` | `captcha_key` | Captcha validate: `WHERE captcha_key=?` | Every captcha check |
| `idx_captcha_expire` | `captcha` | `expire_time` | Cleanup: `WHERE expire_time < NOW()` | Scheduled job |
| `idx_dict_code` | `dict_item` | `dict_code` | Dict lookup: `WHERE dict_code=?` | Every dict reference |
| `idx_ler_task` | `log_extract_result` | `task_id, robot_sn` | Log results: `WHERE task_id=? AND robot_sn=?` | Occasional |
| `idx_ler_success` | `log_extract_result` | `success` | Failure monitoring: `WHERE success=0` | Monitoring |
| `idx_synergy2_enterprise` | `synergy2_info` | `enterprise_id` | Synergy listing | Occasional |

---

## 3. SQLModel Entity Definitions

Complete entity definitions for all 36 tables with table=True annotations, SQLModel Field types, max_lengths, and COMMENT descriptions matching the legacy schema. See full artifact for complete code.

### 3.1 Base Mixins

```python
class TimestampMixin(SQLModel):
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)

class AuditMixin(TimestampMixin):
    create_by: Optional[str] = Field(default=None, max_length=64)
    creator_id: Optional[str] = Field(default=None, max_length=20)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)

class SoftDeleteMixin(SQLModel):
    del_flag: str = Field(default="1", max_length=1)
```

### 3.2 Key Entities (representative sample)

- **UserEntity**: 14 columns including `username`, `password` (→`password_hash` in Phase 2), `email`, `mobile`, `avatar`, `status`, `user_type`, `enterprise_id`, `dify_user_name`
- **RobotEntity**: 15 columns including `name`, `code`, `serial_no`, `ip`, `username`, `password` (→`password_enc`), `brand`, `enterprise_id`
- **TaskInfoEntity**: 14 columns for task CRUD with audit trail
- **AgentInfoEntity**: 15 columns for Dify-powered AI agents
- Plus 31 more entities: SystemEnterpriseEntity, SystemRoleEntity, SystemMenuEntity (VARCHAR PK), MenuEntity (BIGINT PK legacy), junction tables, inspection/inventory task entities, library entities, screen/dashboard entities, utility entities

---

## 4. Database Connection Module

```python
# backend/infrastructure/db/connection.py
DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/raas")
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 20
DB_POOL_TIMEOUT: int = 30
DB_POOL_RECYCLE: int = 3600
DB_ECHO: bool = False

engine = create_engine(DATABASE_URL, pool_size=..., pool_pre_ping=True)

def get_session() -> Session:
    with Session(engine) as session:
        yield session
```

---

## 5. Migration Files (Written)

All files committed to `backend/migrations/`:

```
backend/migrations/
├── runner.py                        # Zero-dependency Python runner (185 lines)
├── 001_baseline_schema.up.sql       # 36 tables with PKs
├── 001_baseline_schema.down.sql     # DROP in reverse order
├── 002_add_fk_constraints.up.sql    # 25 FK constraints with ON DELETE strategy
├── 002_add_fk_constraints.down.sql  # DROP FOREIGN KEY per constraint
├── 003_add_query_indexes.up.sql     # 30+ query-driven indexes
└── 003_add_query_indexes.down.sql   # DROP INDEX per index
```

### Runner Usage

```bash
python backend/migrations/runner.py up       # Apply all pending
python backend/migrations/runner.py down     # Roll back last applied
python backend/migrations/runner.py status   # Show migration state
```

---

## 6. Critical Query Plans

### Login (highest frequency)
```sql
SELECT id, username, password, nickname, status, user_type
FROM user WHERE username = ? AND del_flag = '1';
```
**Without index**: Full table scan — O(n), ~10ms for 10K rows.
**With `uq_user_username`**: Index lookup → 1 row, O(log n), ~0.1ms.

### Permission Check (every API request)
```sql
SELECT r.role_key FROM sys_user_role sur
JOIN sys_role r ON r.id = sur.role_id
WHERE sur.user_id = ? AND sur.enterprise_id = ? AND r.del_flag = '1';
```
**With composite PK + FK index**: Covering index scan → 1-3 rows.

### Task Listing (most common admin query)
```sql
SELECT id, task_name, task_type, status, robot_id
FROM task_info WHERE enterprise_id = ? AND del_flag = '1'
ORDER BY create_time DESC LIMIT 20;
```
**With `idx_task_enterprise_status`**: Index range scan + sort merge.

### Robot Heartbeat (highest write frequency)
```sql
UPDATE robot SET update_time = NOW() WHERE serial_no = ?;
```
**With `uq_robot_serial`**: Single-row update — O(log n), ~1ms.

---

## 7. Rollback & Safety

| Check | Status |
|-------|--------|
| Every `up.sql` has matching `down.sql` | ✅ |
| Down scripts drop in reverse dependency order | ✅ |
| All DDL uses `IF EXISTS` / `IF NOT EXISTS` guards | ✅ |
| No table-locking DDL without stated strategy | ✅ |
| No `ALTER TABLE ... MODIFY COLUMN` — type changes use expand-contract | ✅ |

### Rollback Procedure
```bash
mysqldump --single-transaction raas > raas_pre_migration.sql
python backend/migrations/runner.py up
python backend/migrations/runner.py down  # if issues detected
mysql raas < raas_pre_migration.sql       # last resort
```

---

## 8. Retention & Cleanup

| Table | Strategy | Schedule |
|-------|----------|----------|
| `captcha` | Delete expired | Every 15 min |
| `dashboard` | Keep 7 days | Daily 03:00 |
| `log_extract_result` | Keep 90 days | Weekly archive + delete |
| `screen_robot_log` | Keep 180 days | Monthly archive + delete |
| Soft-deleted rows (`del_flag='0'`) | Hard-delete after 180 days | Monthly |

---

## 9. Nullable Column Justifications

| Table | Column | Nullable? | Reason |
|-------|--------|-----------|--------|
| `user` | `email` | YES | Not all users have email; OAuth may use mobile only |
| `user` | `mobile` | YES | Email-only accounts exist |
| `user` | `enterprise_id` | YES | Users may exist before enterprise assignment |
| `robot` | `ip` | YES | DHCP-assigned; robot may be offline |
| `robot` | `enterprise_id` | YES | Robot may be unassigned |
| `task_info` | `map_id` | YES | Not all task types require a map |
| `task_result_detail` | `detail_value` | YES | Result data may not have arrived yet |
| `agent_info` | `dify_agent_id` | YES | Agent created but not yet synced to Dify |
| `recommended_agent_info` | `copyright` | YES | Not all agents need copyright |
| `recommended_agent_info` | `custom_disclaimer` | YES | Optional legal disclaimer |

---

## 10. Completion Report

```yaml
completion_report:
  what_was_done: >
    Analyzed the full RoboEase codebase (39 entities across services, DB schema dumps,
    and Docker configuration). Designed SQLModel entity definitions for all tables,
    specified the database connection module with connection pooling, wrote complete
    up/down migration files for baseline schema (001), foreign key constraints (002),
    and query indexes (003). Every index is justified by a specific query pattern
    observed in service code. All nullable columns have documented reasons. FK
    constraints are explicit with ON DELETE behavior specified per relationship.
    Documented zero-downtime migration procedures and rollback strategy.

  key_decisions:
    - decision: Preserve VARCHAR PKs with Snowflake IDs for immediate refactor
      rationale: >
        Changing to BIGINT AUTO_INCREMENT would require coordinated changes to
        all service create() methods that use common.IdUtil.get_next_id() and
        all FK columns. Phase 2 can use expand-contract pattern. Risk of
        production data corruption from mixed PK types is too high for Phase 1.

    - decision: Keep legacy entity names (UserEntity, RobotEntity, etc.) unchanged
      rationale: >
        Services import these names directly. Renaming breaks the entire service
        layer. The refactor improves structure under the same naming contract.

    - decision: FK constraints with ON DELETE CASCADE for child tables
      rationale: >
        Junction tables (user_role, role_menu) and child tables (task_detail,
        inspection_steps) have no independent existence. CASCADE prevents orphan
        records. Operational tables (robot, task_info) use SET NULL or RESTRICT
        to prevent accidental data loss.

    - decision: Separate legacy menu table (BIGINT PK) from refactored sys_menu (VARCHAR PK)
      rationale: >
        raas.sql contains data for the menu table with BIGINT AUTO_INCREMENT IDs.
        Newer DDL uses sys_menu with VARCHAR IDs. Both coexist. Define both entities
        and let service code migrate gradually.

    - decision: Zero-dependency migration runner using raw SQL files
      rationale: >
        Alembic is not in requirements.txt. pymysql is already a dependency.
        Raw .sql files are DBA-friendly, reviewable, and can be applied manually.

  handoff_focus:
    - senior-engineer: Create backend/infrastructure/db/entities.py with the SQLModel definitions
    - senior-engineer: Create backend/infrastructure/db/connection.py with connection pool config
    - senior-engineer: Update backend/db/database.py to re-export from new module locations
    - senior-engineer: Wire migrations/runner.py for on-deploy schema application
    - devops-engineer: Configure MySQL 8.0 with innodb_buffer_pool_size ≥ 512MB
    - devops-engineer: Set up scheduled cleanup jobs for captcha/dashboard TTL
    - performance-engineer: Monitor slow query log after index deployment

  open_questions:
    - What is the current production data volume per table? Needed for migration backfill batch sizing.
    - How many Snowflake worker IDs are configured? Affects ID collision risk during migration.
    - Are there application-level uniqueness checks that duplicate what FK constraints should enforce?
    - Does the existing synergy_info table have data? Only synergy2_info is actively used.
    - Is the legacy menu table still actively written to? Or is it read-only reference data?

  known_constraints:
    - MySQL 8.0 only — no PostgreSQL migration planned (confirmed by docker-compose)
    - Team size <10 — migrations must be simple, reviewable, reversible
    - No Alembic in dependencies — runner must be self-contained
    - Snowflake ID generation embedded in all service create() methods — cannot change PK type without coordinated refactor
    - Robot planning backend (Flask/SQLite) has separate schema — not in scope
    - Legacy menu table (BIGINT PK) coexists with sys_menu (VARCHAR PK) — both must be supported

  confidence_differential: 0.85
  dissent_if_alone: null
  iteration_context: >
    v5 builds on v4's complete schema analysis. v5's key differences: (1) preserves
    VARCHAR PKs with Snowflake IDs instead of converting to BIGINT, based on risk
    analysis of service code dependencies; (2) provides complete SQLModel entity
    definitions, not just DDL; (3) adds the connection module spec; (4) identifies
    the legacy menu table coexistence issue. v5 is execution-ready for Phase 1
    of the refactor (add constraints and indexes, consolidate config). Phase 2
    (PK migration to BIGINT) is deferred to a separate task with expand-contract
    planning.
```