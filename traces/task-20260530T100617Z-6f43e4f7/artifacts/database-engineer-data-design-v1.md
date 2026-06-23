# Data Design: RoboEase Refactor — Database Schema & Migration Strategy v4

## Overview

This document is the **execution-ready database design** for the RoboEase v3.0 refactor. It builds on v1–v3 analysis and translates decisions into **working migration files** committed to `backend/migrations/`. Every migration has a paired `up.sql` and `down.sql`. Every index references a specific query pattern. Every nullable column has a documented reason.

### Key Differences from v3

| Aspect | v3 Design | v4 (This) |
|--------|-----------|-----------|
| Migration delivery | Text-embedded SQL snippets | **Real files** in `backend/migrations/` |
| Runner | Text-embedded Python snippet | **Real `backend/migrations/runner.py`** |
| Table count | ~30 tables (some merged) | **39 tables** (matches legacy schema surface) |
| New tables | None | `sys_config`, `notice_user_read` |
| Col renames | `password` → `password_hash` | Same, plus `expire_time` → `expires_at` |
| ID strategy | `BIGINT AUTO_INCREMENT` | Same (consistent) |

---

## 1. Source Evidence

### 1.1 Confirmed Facts

| Fact | Evidence |
|------|----------|
| **MySQL 8.0** with `utf8mb4_general_ci` | `docker/edge/docker-compose.yaml` L97, L139 |
| **DATABASE_URL**: `mysql+pymysql://root:@mysql:3306/raas` | `docker/edge/docker-compose.yaml` L69 |
| **No existing migration framework** | `dbscripts/migrations/` is empty |
| **Ad-hoc DML** for schema changes | `dbscripts/DML/dml_*.sql` files are raw SQL updates |
| **Backward-compat re-exports** | `backend/db/database.py` re-exports from `infrastructure.db.*` |
| **MQTT broker**: EMQX 5.8.4 | `docker/edge/docker-compose.yaml` L167 |
| **Redis 7** for sessions/cache | `docker/edge/docker-compose.yaml` L148 |
| **JWT auth** with HS256 | `backend/config/setting.py`, docker-compose env |
| **No FK constraints** in current schema | `dbscripts/raas.sql` — no `FOREIGN KEY` statements |
| **No indexes beyond PK** | `dbscripts/raas.sql` — no `KEY` or `INDEX` definitions beyond PRIMARY |
| **Plaintext passwords** | Current `dbscripts/raas.sql` stores `password` for robot credentials |
| **String IDs** (varchar(20)) | All primary keys are `varchar(20)` |

### 1.2 Schema Inventory (39 Tables)

| # | Table | Domain | Rows (est.) |
|---|-------|--------|-------------|
| 1 | `sys_enterprise` | Multi-Tenant | <100 |
| 2 | `sys_dept` | Org | <500 |
| 3 | `user` | Identity | <10K |
| 4 | `sys_role` | RBAC | <50 |
| 5 | `sys_menu` | RBAC | <200 |
| 6 | `sys_user_role` | Junction | <50K |
| 7 | `sys_role_menu` | Junction | <5K |
| 8 | `sys_user_enterprise` | Junction | <10K |
| 9 | `sys_config` | Config | <100 |
| 10 | `notice` | Notification | <1K |
| 11 | `notice_user_read` | Junction | <100K |
| 12 | `dict` | Dictionary | <20 |
| 13 | `dict_item` | Dictionary | <200 |
| 14 | `robot` | Robot | <1K |
| 15 | `robot_ext_info` | Robot | <10K |
| 16 | `task_info` | Task | <10K |
| 17 | `task_info_detail` | Task | <100K |
| 18 | `task_result_detail` | Task | <100K |
| 19 | `inspection_task_info` | Inspection | <1K |
| 20 | `inspection_task_steps` | Inspection | <10K |
| 21 | `inspection_task_results` | Inspection | <10K |
| 22 | `inventory_task_info` | Inventory | <1K |
| 23 | `inventory_task_steps` | Inventory | <10K |
| 24 | `inventory_task_results` | Inventory | <10K |
| 25 | `device` | Device | <100 |
| 26 | `agent_info` | Agent | <500 |
| 27 | `recommended_agent_info` | Agent | <50 |
| 28 | `action_library_info` | Library | <100 |
| 29 | `expression_library_info` | Library | <100 |
| 30 | `voice_library_info` | Library | <50 |
| 31 | `knowledge_library_info` | Library | <100 |
| 32 | `screen_project` | Screen | <50 |
| 33 | `screen_page` | Screen | <500 |
| 34 | `screen_robot_log` | Screen | <10K |
| 35 | `synergy_info` | Synergy | <100 |
| 36 | `synergy2_info` | Synergy | <100 |
| 37 | `captcha` | Utility | <1K |
| 38 | `dashboard` | Dashboard | <10K |
| 39 | `log_extract_result` | Logging | <100K |

---

## 2. Design Principles

1. **MySQL 8.0 is the sole target** — confirmed by production docker-compose. Use InnoDB, `utf8mb4_0900_ai_ci`, JSON type, CHECK constraints, CTEs, online DDL.
2. **Normalization by default** — every column earns its place. Denormalization documented explicitly.
3. **FK constraints mandatory** — `ON DELETE RESTRICT` for operational tables; `CASCADE` for junction/tracking tables; `SET NULL` for optional parent relationships.
4. **Nullable only with documented reason** — every nullable column has an inline COMMENT explaining why.
5. **Indexes reference specific query patterns** — no "intuition indexes." Every index in the codebase is justified in section 7.
6. **Up + down migrations always paired** — rollback is written before forward ships.
7. **Zero-downtime for production** — expand-contract pattern; no table-locking DDL without stated strategy.
8. **Naming**: `lowercase_snake_case`, singular table names, `_at` suffix for timestamps, `_by` for audit user IDs, `_enc` for encrypted values.
9. **Soft-delete via `deleted_at DATETIME(3) NULL`** — NULL=active; timestamp enables TTL cleanup.
10. **ID type**: `BIGINT AUTO_INCREMENT` — native MySQL, 8 bytes, 18 quintillion range.

---

## 3. Entity-Relationship Map

```
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
sys_dept ──1:N── sys_dept (self-ref: parent_id)

user ──N:M── sys_role (via sys_user_role)
user ──N:M── sys_enterprise (via sys_user_enterprise)
sys_role ──N:M── sys_menu (via sys_role_menu)

robot ──1:N── robot_ext_info
robot ──1:N── task_info

task_info ──1:N── task_info_detail
task_info ──1:N── task_result_detail
task_info ──1:N── log_extract_result

inspection_task_info ──1:N── inspection_task_steps
inspection_task_info ──1:N── inspection_task_results

inventory_task_info ──1:N── inventory_task_steps
inventory_task_info ──1:N── inventory_task_results

screen_project ──1:N── screen_page
screen_project ──1:N── screen_robot_log

notice ──1:N── notice_user_read
notice_user_read ──N:1── user

dict ──1:N── dict_item (logical, via dict_code)
```

---

## 4. Migration Files (Committed)

```
backend/migrations/
├── runner.py                            # Zero-dependency Python runner
├── 001_baseline_schema.up.sql           # 39 tables, all indexes, all UNIQUE keys
├── 001_baseline_schema.down.sql         # DROP in reverse dependency order
├── 002_add_fk_constraints.up.sql        # 30+ FK constraints
├── 002_add_fk_constraints.down.sql      # DROP FOREIGN KEY statements
├── 003_add_query_indexes.up.sql         # Composite covering indexes
├── 003_add_query_indexes.down.sql       # DROP INDEX statements
├── 004_seed_rbac_data.up.sql            # Default enterprise, admin user, role, menus
├── 004_seed_rbac_data.down.sql          # DELETE seed records
├── 005_add_check_constraints.up.sql     # CHECK constraints (MySQL 8.0.16+)
└── 005_add_check_constraints.down.sql   # DROP CHECK statements
```

### Migration Runner Usage

```bash
# Apply all pending migrations
python backend/migrations/runner.py up

# Roll back the most recent migration
python backend/migrations/runner.py down

# Check migration status
python backend/migrations/runner.py status
```

### Column Renames (Legacy → New)

| Legacy Column | New Column | Table | Reason |
|---------------|------------|-------|--------|
| `password` | `password_hash` | `user` | Clarity: stores hash, not plaintext |
| `password` | `password_enc` | `robot` | Clarity: stores encrypted credential |
| `enterprise_name` | `name` | `sys_enterprise` | Consistency with other tables |
| `expire_time` | `expires_at` | `captcha` | `_at` suffix convention |
| `create_time` | `created_at` | all | `_at` suffix convention |
| `update_time` | `updated_at` | all | `_at` suffix convention |
| `create_by` | `created_by` | all | Past tense convention |
| `update_by` | `updated_by` | all | Past tense convention |
| `del_flag` | `deleted_at` | all | Timestamp enables TTL cleanup |

### New Columns Added

| New Column | Table | Type | Rationale |
|------------|-------|------|-----------|
| `status` | `robot` | TINYINT | Explicit online/offline tracking |
| `step_num` | `task_info_detail` | INT | Ordered execution guarantee |
| `step_num` | `inspection_task_steps` | INT | Ordered execution guarantee |
| `step_num` | `inventory_task_steps` | INT | Ordered execution guarantee |
| `dept_id` | `user` | BIGINT NULL | Department assignment (optional) |
| `published_at` | `notice` | DATETIME(3) | Published timestamp tracking |
| `priority` | `notice` | TINYINT | Notification urgency |
| `target_type` | `notice` | TINYINT | Granular notice targeting |
| `target_id` | `notice` | BIGINT NULL | Target entity reference |
| `snapshot_at` | `dashboard` | DATETIME(3) | Renamed from `create_time` |

---

## 5. Critical Design Decisions

### 5.1 BIGINT AUTO_INCREMENT vs Snowflake VARCHAR

**Decision**: Use `BIGINT AUTO_INCREMENT` for all primary keys.

**Rationale**:
- MySQL 8.0 native auto_increment is 8 bytes vs varchar(20) = 21 bytes (+ length prefix)
- B-tree index comparisons on BIGINT are integer ops (~1 cycle) vs string ops (~10+ cycles)
- MySQL InnoDB uses PK as clustered index — smaller PK = smaller secondary indexes
- AUTO_INCREMENT produces sequential inserts = no page splits = better write throughput
- Snowflake IDs can be reconstructed from `created_at` + `id` if needed

**Migration path**: If existing production data uses snowflake VARCHAR IDs, add a `legacy_id` column and map in a data migration step.

### 5.2 deleted_at (DATETIME NULL) vs del_flag (CHAR '1'/'0')

**Decision**: Use `deleted_at DATETIME(3) NULL` for all soft-delete columns.

**Rationale**:
- NULL=active is idiomatic SQL; IS NULL / IS NOT NULL predicates are optimizable
- Timestamp records WHEN deletion occurred — enables TTL cleanup ("hard delete after 180 days")
- No separate audit column needed for deletion timestamp
- Compatible across all MySQL versions

### 5.3 FK Strategy: RESTRICT vs CASCADE

**Decision**: Use CASCADE for junction/child tables, RESTRICT for parent operational tables.

| Relationship | ON DELETE | Reason |
|-------------|-----------|--------|
| `sys_role` → `sys_enterprise` | CASCADE | Roles belong to enterprise; if enterprise deleted, roles go too |
| `user` → `sys_dept` | SET NULL | User may be reassigned; don't cascade delete the user |
| `robot` → `sys_enterprise` | SET NULL | Robot may survive enterprise deletion for reassignment |
| `task_info` → `sys_enterprise` | CASCADE | Tasks belong to enterprise |
| `task_info_detail` → `task_info` | CASCADE | Details are meaningless without parent task |
| `sys_user_role` → `user` | CASCADE | Junction — delete assignments when user deleted |
| `sys_role_menu` → `sys_role` | CASCADE | Junction — delete assignments when role deleted |

### 5.4 JSON vs Normalized Tables for Libraries

**Decision**: Store library content (actions, expressions, voices, knowledge) as JSON columns, not normalized tables.

**Rationale**:
- Library entries are always read/written as complete arrays (never queried for individual items at DB level)
- MySQL 8.0 JSON type provides validation and some indexing via virtual columns
- 100 actions × 100 libraries = 10K rows if normalized — but they're always loaded together
- No cross-library queries or aggregation on individual items
- JSON keeps the data model simple and matches the application's mental model

**Trade-off**: Cannot query "find all libraries containing action #146" via SQL. Mitigation: add a virtual column index on `action_info` if this query pattern emerges.

### 5.5 No `sys_dept` in the Legacy Schema — Why Add It?

**Decision**: Add `sys_dept` table (not in legacy `raas.sql`).

**Rationale**:
- Frontend admin mock includes `/dept` API endpoints (`dept.mock.ts`)
- Admin menu references include "部门管理" (department management) with full CRUD perms
- `user.dept_id` foreign key is present in older SQL dumps and matches the entity model
- Adding it now avoids a later migration to retrofit the relationship

---

## 6. Index Justification Reference

Every index in this schema references a specific query pattern:

| Index | Table | Query Pattern | Frequency |
|-------|-------|---------------|-----------|
| `uq_user_username` | `user` | `SELECT * FROM user WHERE username = ? AND deleted_at IS NULL` | Every login attempt |
| `uq_user_email` | `user` | `SELECT * FROM user WHERE email = ? AND deleted_at IS NULL` | Email-based login, uniqueness check |
| `uq_user_mobile` | `user` | `SELECT * FROM user WHERE mobile = ? AND deleted_at IS NULL` | Mobile login |
| `idx_user_status` | `user` | `SELECT * FROM user WHERE status=1 ORDER BY created_at DESC LIMIT 20` | Admin user listing |
| `idx_dept_parent` | `sys_dept` | `SELECT * FROM sys_dept WHERE parent_id = ?` | Tree navigation |
| `uq_dept_code` | `sys_dept` | `SELECT * FROM sys_dept WHERE code = ? AND deleted_at IS NULL` | Uniqueness enforcement |
| `uq_role_key_ent` | `sys_role` | `SELECT * FROM sys_role WHERE enterprise_id=? AND role_key=? AND deleted_at IS NULL` | Every permission check |
| `idx_menu_parent` | `sys_menu` | `SELECT * FROM sys_menu WHERE parent_id = ?` | Menu tree rendering |
| `idx_menu_type` | `sys_menu` | `SELECT * FROM sys_menu WHERE menu_type = 'F'` | Permission aggregation |
| `uq_robot_serial` | `robot` | `SELECT * FROM robot WHERE serial_no = ? AND deleted_at IS NULL` | Robot heartbeat — every few seconds per robot |
| `uq_robot_code` | `robot` | `SELECT * FROM robot WHERE code = ? AND deleted_at IS NULL` | Robot management operations |
| `idx_robot_enterprise` | `robot` | `SELECT * FROM robot WHERE enterprise_id = ? AND deleted_at IS NULL` | Enterprise robot listing |
| `idx_robot_type` | `robot` | `SELECT * FROM robot WHERE robot_type = ? AND deleted_at IS NULL` | Filter by robot type |
| `idx_robot_status` | `robot` | `SELECT * FROM robot WHERE status = 1` | Online robot monitoring |
| `idx_robot_ent_status` | `robot` | `SELECT * FROM robot WHERE enterprise_id=? AND status=?` | Enterprise status filter |
| `idx_task_enterprise_status` | `task_info` | `SELECT * FROM task_info WHERE enterprise_id=? AND status=? LIMIT 20` | Most common admin query |
| `idx_task_ent_status_created` | `task_info` | Same as above + `ORDER BY created_at DESC` — covering index | Paginated listing |
| `idx_task_robot` | `task_info` | `SELECT * FROM task_info WHERE robot_id = ?` | Robot detail page |
| `idx_task_type` | `task_info` | `SELECT * FROM task_info WHERE enterprise_id=? AND task_type=?` | Task type filter |
| `uq_task_name_ent` | `task_info` | Duplicate name detection per enterprise | Form validation |
| `idx_rei_robot` | `robot_ext_info` | `SELECT * FROM robot_ext_info WHERE robot_id = ?` | Robot config listing |
| `idx_rei_robot_type` | `robot_ext_info` | `SELECT * FROM robot_ext_info WHERE robot_id=? AND ext_type=?` | Filtered config lookup |
| `uq_rei_robot_type_code` | `robot_ext_info` | Uniqueness per robot+type+code | Prevent duplicates |
| `idx_trd_task_robot` | `task_result_detail` | `SELECT * FROM task_result_detail WHERE task_id=? AND robot_sn=?` | Task execution status |
| `idx_trd_status` | `task_result_detail` | `SELECT * FROM task_result_detail WHERE status=2 ORDER BY created_at DESC` | Monitoring — recent failures |
| `idx_insp_task_enterprise` | `inspection_task_info` | `SELECT * FROM inspection_task_info WHERE enterprise_id=?` | Inspection listing |
| `idx_insp_task_robot` | `inspection_task_info` | `SELECT * FROM inspection_task_info WHERE robot_sn=?` | Per-robot inspection history |
| `idx_device_enterprise` | `device` | `SELECT * FROM device WHERE enterprise_id=?` | Device listing |
| `uq_device_ent_sn` | `device` | `SELECT * FROM device WHERE enterprise_id=? AND sn=? AND deleted_at IS NULL` | Device registration |
| `idx_agent_enterprise` | `agent_info` | `SELECT * FROM agent_info WHERE enterprise_id=?` | Agent listing |
| `idx_agent_dify` | `agent_info` | `SELECT * FROM agent_info WHERE dify_agent_id=?` | Dify webhook callback |
| `idx_agent_device_type_code` | `agent_info` | `SELECT * FROM agent_info WHERE agent_device_type=? AND agent_device_code=?` | Device-agent mapping |
| `idx_rec_agent_category_pos` | `recommended_agent_info` | `SELECT * FROM recommended_agent_info ORDER BY category, position` | Agent marketplace |
| `idx_rec_agent_install` | `recommended_agent_info` | `SELECT * FROM recommended_agent_info ORDER BY install_count DESC LIMIT 10` | Popular agents |
| `idx_ali_enterprise_type` | `action_library_info` | `SELECT * FROM action_library_info WHERE enterprise_id=? AND robot_type=?` | Action library listing |
| `idx_screen_project_name` | `screen_project` | `SELECT * FROM screen_project WHERE project_name LIKE ?%` | Project search |
| `idx_sp_project` | `screen_page` | `SELECT * FROM screen_page WHERE project_id=?` | Project detail page |
| `idx_srl_project` | `screen_robot_log` | `SELECT * FROM screen_robot_log WHERE project_id=? ORDER BY created_at DESC` | Project operation log |
| `idx_captcha_expires` | `captcha` | `DELETE FROM captcha WHERE expires_at < NOW()` | Scheduled cleanup |
| `idx_dashboard_time` | `dashboard` | `SELECT * FROM dashboard ORDER BY snapshot_at DESC LIMIT 1` | Latest snapshot |
| `idx_ler_task_robot` | `log_extract_result` | `SELECT * FROM log_extract_result WHERE task_id=? AND robot_sn=? ORDER BY created_at DESC` | Log extraction results |
| `idx_ler_failed` | `log_extract_result` | `SELECT * FROM log_extract_result WHERE success=0 ORDER BY created_at DESC` | Failure monitoring |
| `idx_notice_type_status` | `notice` | `SELECT * FROM notice WHERE notice_type=? AND status=1` | Active notice listing |
| `idx_notice_published` | `notice` | `SELECT * FROM notice WHERE status=1 ORDER BY published_at DESC` | Latest notices |
| `idx_di_dict_code_sort` | `dict_item` | `SELECT * FROM dict_item WHERE dict_code=? ORDER BY sort_no` | Dictionary lookup |

---

## 7. Critical Query Plans

### 7.1 Login (highest frequency)

```sql
SELECT id, username, password_hash, status, user_type
FROM user
WHERE username = ? AND deleted_at IS NULL;
```

**Expected plan**: Index lookup on `uq_user_username (username, deleted_at)` — 1 row, O(log n).

### 7.2 Permission Check (every API request)

```sql
SELECT r.role_key, r.data_scope
FROM sys_user_role sur
JOIN sys_role r ON r.id = sur.role_id
WHERE sur.user_id = ? AND sur.enterprise_id = ? AND r.deleted_at IS NULL;
```

**Expected plan**: Index scan on `uq_user_role_ent (enterprise_id, user_id, role_id)` for junction → PK lookup on `sys_role`. 1–3 rows.

### 7.3 Task Listing (most common admin query)

```sql
SELECT ti.id, ti.task_name, ti.task_type, ti.status, r.name AS robot_name
FROM task_info ti
JOIN robot r ON r.id = ti.robot_id
WHERE ti.enterprise_id = ? AND ti.status = ? AND ti.deleted_at IS NULL
ORDER BY ti.created_at DESC
LIMIT 20 OFFSET ?;
```

**Expected plan**:
```
→ Index: idx_task_ent_status_created (enterprise_id, status, created_at)
→ Backward index scan (DESC)
→ Nested loop join to robot via PK
→ LIMIT applied after 20 rows found
```

### 7.4 Robot Heartbeat (highest write frequency)

```sql
UPDATE robot SET updated_at = NOW(), status = 1 WHERE serial_no = ?;
```

**Expected plan**: Index lookup on `uq_robot_serial` → single row update. O(log n), ~1ms.

### 7.5 Dashboard Latest Snapshot

```sql
SELECT * FROM dashboard ORDER BY snapshot_at DESC LIMIT 1;
```

**Expected plan**: Backward index scan on `idx_dashboard_time (snapshot_at)` → 1 row. O(1).

---

## 8. Retention & Cleanup

| Table | Strategy | Schedule | SQL |
|-------|----------|----------|-----|
| `captcha` | Delete expired | Every 15 min | `DELETE FROM captcha WHERE expires_at < NOW()` |
| `dashboard` | Keep 7 days | Daily 03:00 | `DELETE FROM dashboard WHERE snapshot_at < NOW() - INTERVAL 7 DAY` |
| `log_extract_result` | Keep 90 days | Weekly | Archive then delete |
| `screen_robot_log` | Keep 180 days | Monthly | Archive then delete |
| Soft-deleted rows | Hard-delete | Monthly | `DELETE FROM {table} WHERE deleted_at < NOW() - INTERVAL 180 DAY` |

---

## 9. Zero-Downtime Migration Strategy

For any production schema change, use the **expand-contract** pattern:

```
Phase 1: EXPAND    — ALTER TABLE ADD COLUMN (nullable, no DEFAULT that rewrites table)
Phase 2: DUAL-WRITE — Application writes to both old and new columns
Phase 3: BACKFILL  — UPDATE in batches of 5000 rows with sleep between batches
Phase 4: TRANSITION — Application reads from new column only
Phase 5: CONTRACT  — ALTER TABLE DROP COLUMN in a follow-up migration
```

MySQL 8.0 **online DDL** (no table lock):
- `ALTER TABLE ... ADD COLUMN ... NULL` — INSTANT in 8.0.12+
- `ALTER TABLE ... ADD INDEX` — only metadata lock (ALGORITHM=INPLACE)
- `ALTER TABLE ... ADD FOREIGN KEY` — online with `ALGORITHM=INPLACE`

Avoid these locking operations in production:
- `ALTER TABLE ... MODIFY COLUMN type` — table rebuild
- `ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT 'x'` — table rebuild in older MySQL
- `ALTER TABLE ... DROP COLUMN` — INSTANT in 8.0.29+, table rebuild before

---

## 10. Completion Report

```yaml
completion_report:
  what_was_done: >
    Designed and wrote the complete database schema for the RoboEase v3.0 refactor.
    Created 11 migration files (5 up + 5 down + 1 runner) totaling 39 tables, 30+
    foreign key constraints, 45+ indexes, and 15 check constraints. Every migration
    has a paired rollback. Every index references a specific query pattern.
    Created a portable, zero-dependency migration runner (runner.py) that tracks
    applied migrations in a __migrations table. Fixed critical gaps: FK enforcement,
    index coverage, password column naming, soft-delete strategy, and enum constraints.

  key_decisions:
    - decision: Use BIGINT AUTO_INCREMENT for all PKs
      rationale: >
        MySQL InnoDB clustered index performance. 8 bytes vs 21 for VARCHAR(20).
        Integer comparisons are ~10x faster than string. Sequential inserts avoid
        B-tree page splits. Collation-safe (no charset surprise in PK comparisons).

    - decision: Use deleted_at DATETIME(3) NULL instead of del_flag CHAR(1)
      rationale: >
        NULL semantics are well-optimized. Timestamp enables TTL-based hard-delete
        cleanup (DELETE WHERE deleted_at < NOW() - INTERVAL 180 DAY). Single column
        replaces del_flag + audit timestamp.

    - decision: ON DELETE CASCADE for junction tables, SET NULL for optional parent FKs
      rationale: >
        Junction tables have no independent existence. SET NULL on optional parents
        (robot.enterprise_id, user.dept_id) prevents accidental cascade deletion of
        operational data when a tenant or department is deleted.

    - decision: No Alembic dependency — use raw SQL + Python runner
      rationale: >
        Alembic is not in requirements.txt. Adding a dependency for migrations
        is a deployment risk. The runner.py is 160 lines of pure Python with
        pymysql (already a dependency). Migrations are raw .sql files — DBA-friendly,
        reviewable, and can be applied manually if needed.

    - decision: Keep existing table names (sys_menu, sys_role, robot, etc.)
      rationale: >
        Table renames would break all application code, API routes, and frontend
        mocks simultaneously. The refactor improves structure (types, constraints,
        indexes) while preserving the naming contract.

    - decision: Add sys_dept, sys_config, notice_user_read as new tables
      rationale: >
        These tables are implied by frontend mock data and API contracts but are
        missing from the legacy raas.sql dump. Adding them now avoids retrofitting
        migrations later.

  handoff_focus:
    - senior-engineer: Update SQLModel entity definitions to match new column names (password→password_hash, create_time→created_at, etc.)
    - senior-engineer: Update all repository/service code that references old column names
    - senior-engineer: Add password hashing (bcrypt/argon2id) for user.password_hash before production
    - senior-engineer: Wire migration runner into startup (run on deploy, not on every restart)
    - devops-engineer: Set up MySQL connection pooling (ProxySQL or app-level)
    - devops-engineer: Configure scheduled cleanup jobs for captcha/dashboard/soft-delete TTL
    - performance-engineer: Monitor query performance on tables >10K rows after migration

  open_questions:
    - What is the current production data volume per table? Needed for precise EXPLAIN cost estimates.
    - How are Snowflake VARCHAR IDs generated in the legacy codebase? Need the generator config for data migration.
    - Does the application code have hard-coded references to `del_flag = '1'` string comparisons?
    - Are there any application-level uniqueness checks that duplicate what FK constraints should enforce?
    - How is the `action_info` JSON field queried in application code? Should we add MySQL virtual column indexes?

  known_constraints:
    - MySQL 8.0 only — no PostgreSQL migration planned (confirmed by docker-compose)
    - Team size <10 — migrations must be simple and reviewable
    - No Alembic in dependencies — runner must stay self-contained
    - Legacy VARCHAR IDs exist in production — data migration needed for BIGINT conversion
    - Robot planning backend (Flask/SQLite) has separate schema — not in scope
    - Existing production data must be preserved during migration

  confidence_differential: 0.80
  dissent_if_alone: null
  iteration_context: >
    This is v4 of the database design. v1 targeted PostgreSQL (overtaken by evidence).
    v2 added MySQL dual-support. v3 finalized MySQL-only target and established
    the 30-table entity inventory. v4 (this) is the execution-ready version with
    committed migration files, a working runner, and all index justifications
    traceable to specific query patterns.
```