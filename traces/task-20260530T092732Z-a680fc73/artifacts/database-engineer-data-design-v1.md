## Data Design: RoboEase Refactor — Database Schema & Migration Strategy v2

### Artifact Location
`artifacts/database-engineer-data-design-v2.md` (1,605 lines, 78KB)

### Summary

Designed a comprehensive refactored database schema targeting **MySQL 8.0** (confirmed by `docker/edge/docker-compose.yaml`), correcting the PostgreSQL assumption from the prior v1 artifact.

#### Deliverables

**30 Table Definitions** with full DDL in MySQL 8.0 syntax (InnoDB, utf8mb4_0900_ai_ci):
- Identity & Auth: `user`, `sys_role`, `sys_menu`, `sys_dept`, `sys_user_role`, `sys_role_menu`, `sys_user_enterprise`
- Enterprise: `sys_enterprise`
- Robot: `robot`, `robot_ext_info`
- Task: `task_info`, `task_info_detail`, `task_result_detail`
- Utility: `captcha`, `dict`, `dict_item`, `sys_config`
- Communication: `notice`, `notice_user_read`
- Dashboard: `dashboard`
- Screen Project: `screen_project`, `screen_page`, `screen_robot_log`
- Agent: `agent_info`, `recommended_agent_info`
- Libraries: `action_library_info`, `expression_library_info`, `voice_library_info`, `knowledge_library_info`
- Synergy: `synergy_info`, `synergy2_info`
- Device: `device`
- Logging: `log_extract_result`

**4 Sequential Migrations** (each with up.sql and down.sql):
1. `001_baseline_schema` — All table creation with inline indexes
2. `002_add_fk_constraints` — 28 foreign key constraints with ON DELETE strategy
3. `003_add_query_indexes` — Performance indexes with query-pattern justifications
4. `004_add_audit_triggers` — 21 BEFORE UPDATE triggers for auto-updated_at

**Index Justifications**: 26 indexes each mapped to a specific frontend query pattern (e.g., `uq_robot_serial` for heartbeat UPDATE, `idx_task_enterprise_status` for paginated task listing).

**EXPLAIN Analysis**: 4 critical queries analyzed (task listing, robot heartbeat, user login, unread notice count).

**Retention Policy**: Cleanup events for captcha (1h), dashboard (7d), logs (90-180d), soft-deleted rows (180d).

**MySQL Configuration**: Production-ready my.cnf for edge deployment (4GB RAM profile) with InnoDB tuning, slow query logging, binary logging, and event scheduler.

#### Key Design Decisions
- **MySQL 8.0** (not PostgreSQL) — confirmed by docker-compose
- **BIGINT AUTO_INCREMENT** for PKs — optimal B-tree performance
- **DATETIME(3)** for millisecond-precision timestamps
- **JSON type** for variable-schema payloads (task steps, library data)
- **deleted_at IS NULL** for soft-delete with TTL cleanup
- **ON DELETE RESTRICT** for operational entities, **CASCADE** for junction tables
- **CHECK constraints** for enum validation
- **All nullable columns documented** with explicit rationale

#### Confidence Differential
**0.65** — Schema design is derived from frontend API contracts and mock data, not backend source code. Production data volumes, heartbeat frequency, and password encryption method are unknown.