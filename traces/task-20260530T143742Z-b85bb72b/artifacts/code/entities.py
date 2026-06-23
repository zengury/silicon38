"""
SQLModel entity definitions — one class per database table.

All entities live here so they can be imported from a single location.
The legacy `db/database.py` re-exports from this module for backward
compatibility.

Table name → Class name mapping follows the convention:
    snake_case table → PascalCase + "Entity" suffix
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import SQLModel, Field, Column, JSON


# ═══════════════════════════════════════════════════════════════════════
# Base entity mixins
# ═══════════════════════════════════════════════════════════════════════


class BaseEntity(SQLModel):
    """Mixin with standard audit fields included in most tables."""

    id: str = Field(primary_key=True, max_length=40)
    del_flag: str = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class BaseEntityInclusUserOpt(SQLModel):
    """Mixin with audit fields sans del_flag — for tables that never soft-delete."""

    id: str = Field(primary_key=True, max_length=40)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# User & Enterprise
# ═══════════════════════════════════════════════════════════════════════


class UserEntity(SQLModel, table=True):
    """User account — maps to the `user` table."""

    __tablename__ = "user"

    id: str = Field(primary_key=True, max_length=20)
    username: Optional[str] = Field(default=None, max_length=20)
    password: Optional[str] = Field(default=None, max_length=100)
    nickname: Optional[str] = Field(default=None, max_length=30)
    gender: Optional[str] = Field(default="1", max_length=1)
    email: Optional[str] = Field(default=None, max_length=30)
    mobile: Optional[str] = Field(default=None, max_length=20)
    avatar: Optional[str] = Field(default=None, max_length=255)
    user_type: Optional[str] = Field(default="1", max_length=1)
    status: Optional[str] = Field(default="1", max_length=1)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)

    # Runtime-only fields (not persisted)
    enterprise_id: Optional[str] = None
    dify_user_name: Optional[str] = None


class SystemEnterpriseEntity(SQLModel, table=True):
    """Enterprise / organization — maps to `sys_enterprise`."""

    __tablename__ = "sys_enterprise"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_name: Optional[str] = Field(default=None, max_length=50)
    enterprise_type: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default="0", max_length=1)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class SystemUserEnterpriseEntity(SQLModel, table=True):
    """User-enterprise association — maps to `sys_user_enterprise`."""

    __tablename__ = "sys_user_enterprise"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    enterprise_id: Optional[str] = Field(default=None, max_length=20)
    user_id: Optional[str] = Field(default=None, max_length=20)


# ═══════════════════════════════════════════════════════════════════════
# Role & Permission (RBAC)
# ═══════════════════════════════════════════════════════════════════════


class SystemRoleEntity(SQLModel, table=True):
    """Role definition — maps to `sys_role`."""

    __tablename__ = "sys_role"

    id: str = Field(primary_key=True, max_length=20)
    role_name: str = Field(default="", max_length=30)
    role_key: str = Field(default="", max_length=100)
    role_sort: int = Field(default=0)
    data_scope: Optional[str] = Field(default="1", max_length=1)
    menu_check_strictly: Optional[int] = Field(default=1)
    dept_check_strictly: Optional[int] = Field(default=1)
    status: Optional[str] = Field(default="1", max_length=1)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)
    remark: Optional[str] = Field(default=None, max_length=500)
    enterprise_id: Optional[str] = Field(default=None, max_length=20)


class SystemUserRoleEntity(SQLModel, table=True):
    """User-role association — maps to `sys_user_role`."""

    __tablename__ = "sys_user_role"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    user_id: Optional[str] = Field(default=None, max_length=20)
    role_id: Optional[str] = Field(default=None, max_length=20)


class SystemRoleMenuEntity(SQLModel, table=True):
    """Role-menu permission association — maps to `sys_role_menu`."""

    __tablename__ = "sys_role_menu"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    role_id: Optional[str] = Field(default=None, max_length=20)
    menu_id: Optional[str] = Field(default=None, max_length=20)


class SystemMenuEntity(SQLModel, table=True):
    """Menu / permission tree — maps to `sys_menu`."""

    __tablename__ = "sys_menu"

    id: str = Field(primary_key=True, max_length=20)
    menu_name: str = Field(default="", max_length=50)
    menu_title: Optional[str] = Field(default=None, max_length=100)
    redirect: Optional[str] = Field(default=None, max_length=200)
    parent_id: Optional[str] = Field(default="0", max_length=20)
    order_num: Optional[int] = Field(default=0)
    path: Optional[str] = Field(default="", max_length=200)
    component: Optional[str] = Field(default=None, max_length=255)
    query_param: Optional[str] = Field(default=None, max_length=255)
    is_frame: Optional[int] = Field(default=0)
    is_cache: Optional[int] = Field(default=1)
    menu_type: Optional[str] = Field(default="", max_length=1)
    visible: Optional[str] = Field(default="1", max_length=1)
    status: Optional[str] = Field(default="1", max_length=1)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    perms: Optional[str] = Field(default=None, max_length=100)
    icon: Optional[str] = Field(default="#", max_length=100)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)
    remark: Optional[str] = Field(default="", max_length=500)

    # Tree traversal helpers (not persisted — set at runtime after query)


# ═══════════════════════════════════════════════════════════════════════
# Robot & Device
# ═══════════════════════════════════════════════════════════════════════


class RobotEntity(SQLModel, table=True):
    """Robot device — maps to `robot`."""

    __tablename__ = "robot"

    id: str = Field(primary_key=True, max_length=40)
    name: Optional[str] = Field(default=None, max_length=30)
    code: Optional[str] = Field(default=None, max_length=30)
    ip: Optional[str] = Field(default=None, max_length=15)
    username: Optional[str] = Field(default=None, max_length=20)
    password: Optional[str] = Field(default=None, max_length=30)
    brand: Optional[str] = Field(default=None, max_length=30)
    serial_no: str = Field(default="", max_length=30)
    robot_type: Optional[str] = Field(default="xiaqi", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    create_by: Optional[str] = Field(default=None, max_length=30)
    update_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=30)
    creator_id: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=64)
    del_flag: Optional[str] = Field(default="1", max_length=1)


class RobotExtInfoEntity(SQLModel, table=True):
    """Robot extended info — maps to `robot_ext_info`."""

    __tablename__ = "robot_ext_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: Optional[str] = Field(default=None, max_length=20)
    robot_id: Optional[str] = Field(default=None, max_length=40)
    robot_code: Optional[str] = Field(default=None, max_length=30)
    ext_type: Optional[str] = Field(default=None, max_length=50)
    ext_value: Optional[str] = Field(default=None, max_length=500)
    ext_code: Optional[str] = Field(default=None, max_length=50)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class DeviceInfoEntity(SQLModel, table=True):
    """Device info — maps to `device_info`."""

    __tablename__ = "device_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    device_name: str = Field(default="", max_length=255)
    device_type: str = Field(default="", max_length=50)
    device_sn: str = Field(default="", max_length=255)
    device_description: Optional[str] = Field(default=None, max_length=255)
    device_status: Optional[str] = Field(default=None, max_length=1)
    device_config: Optional[str] = Field(default=None, max_length=65535)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Dashboard, Captcha, Screen
# ═══════════════════════════════════════════════════════════════════════


class DashboardEntity(SQLModel, table=True):
    """Dashboard metrics — maps to `dashboard`."""

    __tablename__ = "dashboard"

    id: str = Field(primary_key=True, max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    robot_total_today: Optional[int] = Field(default=0)
    robot_total_all: Optional[int] = Field(default=0)
    runtime_total_today: Optional[float] = Field(default=None)
    runtime_total_all: Optional[float] = Field(default=None)
    logs_total_today: Optional[int] = Field(default=None)
    logs_total_all: Optional[int] = Field(default=None)


class CaptchaEntity(SQLModel, table=True):
    """Captcha challenge — maps to `captcha`."""

    __tablename__ = "captcha"

    id: str = Field(primary_key=True, max_length=20)
    captcha_key: str = Field(default="", max_length=30)
    captcha_value: int = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    expire_time: Optional[datetime] = Field(default=None)


class ScreenProjectEntity(SQLModel, table=True):
    """Screen project — maps to `screen_project`."""

    __tablename__ = "screen_project"

    id: str = Field(primary_key=True, max_length=30)
    project_name: Optional[str] = Field(default=None, max_length=50)
    customer: Optional[str] = Field(default=None, max_length=50)
    robot_url: Optional[str] = Field(default=None, max_length=255)
    screen_url: Optional[str] = Field(default=None, max_length=255)
    create_time: Optional[datetime] = Field(default=None)
    task_detail_path: Optional[str] = Field(default=None, max_length=500)
    task_file_path: Optional[str] = Field(default=None, max_length=500)
    create_by: Optional[str] = Field(default=None, max_length=64)
    update_by: Optional[str] = Field(default=None, max_length=64)
    creator_id: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=64)
    update_time: Optional[datetime] = Field(default=None)
    del_flag: Optional[str] = Field(default="1", max_length=1)


class ScreenPageEntity(SQLModel, table=True):
    """Screen page — maps to `screen_page`."""

    __tablename__ = "screen_page"

    id: str = Field(primary_key=True, max_length=30)
    project_id: Optional[str] = Field(default=None, max_length=30)
    page_name: Optional[str] = Field(default=None, max_length=50)
    page_url: Optional[str] = Field(default=None, max_length=255)
    sort_order: Optional[int] = Field(default=0)
    create_time: Optional[datetime] = Field(default=None)
    create_by: Optional[str] = Field(default=None, max_length=64)
    update_by: Optional[str] = Field(default=None, max_length=64)
    creator_id: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=64)
    update_time: Optional[datetime] = Field(default=None)
    del_flag: Optional[str] = Field(default="1", max_length=1)


class ScreenRobotLogEntity(SQLModel, table=True):
    """Screen robot log — maps to `screen_robot_log`."""

    __tablename__ = "screen_robot_log"

    id: str = Field(primary_key=True, max_length=20)
    project_id: Optional[str] = Field(default=None, max_length=30)
    robot_id: Optional[str] = Field(default=None, max_length=40)
    log_content: Optional[str] = Field(default=None)
    create_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Dict (Dictionary)
# ═══════════════════════════════════════════════════════════════════════


class DictEntity(SQLModel, table=True):
    """Dictionary type — maps to `dict`."""

    __tablename__ = "dict"

    id: str = Field(primary_key=True, max_length=20)
    name: Optional[str] = Field(default=None, max_length=30)
    dict_code: Optional[str] = Field(default=None, max_length=20)
    status: Optional[int] = Field(default=None)
    items: Optional[str] = Field(default=None, sa_column=Column(JSON))


class DictItemEntity(SQLModel, table=True):
    """Dictionary item — maps to `dict_item`."""

    __tablename__ = "dict_item"

    id: str = Field(primary_key=True, max_length=20)
    dict_id: Optional[str] = Field(default=None, max_length=20)
    label: Optional[str] = Field(default=None, max_length=30)
    value: Optional[str] = Field(default=None, max_length=30)
    status: Optional[int] = Field(default=None)
    sort_order: Optional[int] = Field(default=0)


# ═══════════════════════════════════════════════════════════════════════
# Menu (legacy — separate from sys_menu)
# ═══════════════════════════════════════════════════════════════════════


class MenuEntity(SQLModel, table=True):
    """Legacy menu — maps to `menu`."""

    __tablename__ = "menu"

    id: str = Field(primary_key=True, max_length=20)
    name: Optional[str] = Field(default=None, max_length=30)
    menu_code: Optional[str] = Field(default=None, max_length=20)
    status: Optional[int] = Field(default=None)
    items: Optional[str] = Field(default=None, sa_column=Column(JSON))


# ═══════════════════════════════════════════════════════════════════════
# Task — General
# ═══════════════════════════════════════════════════════════════════════


class TaskInfoEntity(SQLModel, table=True):
    """Task definition — maps to `task_info`."""

    __tablename__ = "task_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: Optional[str] = Field(default=None, max_length=20)
    robot_id: Optional[str] = Field(default=None, max_length=40)
    map_id: Optional[str] = Field(default=None, max_length=255)
    task_type: Optional[str] = Field(default=None, max_length=50)
    task_name: str = Field(default="", max_length=255)
    remark: Optional[str] = Field(default=None, max_length=500)
    status: Optional[str] = Field(default=None, max_length=1)
    task_api_url: Optional[str] = Field(default=None, max_length=255)
    robot_sn: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class TaskInfoDetailEntity(SQLModel, table=True):
    """Task detail steps — maps to `task_info_detail`."""

    __tablename__ = "task_info_detail"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    task_id: Optional[str] = Field(default=None, max_length=20)
    step_name: Optional[str] = Field(default=None, max_length=255)
    detail_type: Optional[str] = Field(default=None, max_length=50)
    detail_value: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class TaskResultDetailEntity(SQLModel, table=True):
    """Task execution result — maps to `task_result_detail`."""

    __tablename__ = "task_result_detail"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    task_id: Optional[str] = Field(default=None, max_length=20)
    result_type: Optional[str] = Field(default=None, max_length=50)
    result_value: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Task — Inspection
# ═══════════════════════════════════════════════════════════════════════


class InspectionTaskInfoEntity(SQLModel, table=True):
    """Inspection task — maps to `inspection_task_info`."""

    __tablename__ = "inspection_task_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    task_name: str = Field(default="", max_length=255)
    task_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    robot_sn: str = Field(default="", max_length=255)
    task_status: str = Field(default="", max_length=1)
    snapshot_interval: Optional[int] = Field(default=None)
    map_id: Optional[str] = Field(default=None, max_length=255)
    map_name: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class InspectionTaskStepsEntity(SQLModel, table=True):
    """Inspection task steps — maps to `inspection_task_steps`."""

    __tablename__ = "inspection_task_steps"

    id: str = Field(primary_key=True, max_length=20)
    inspection_task_id: str = Field(default="", max_length=20)
    steps: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class InspectionTaskResultsEntity(SQLModel, table=True):
    """Inspection task results — maps to `inspection_task_results`."""

    __tablename__ = "inspection_task_results"

    id: str = Field(primary_key=True, max_length=20)
    inspection_task_id: str = Field(default="", max_length=20)
    task_results: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Task — Inventory
# ═══════════════════════════════════════════════════════════════════════


class InventoryTaskInfoEntity(SQLModel, table=True):
    """Inventory task — maps to `inventory_task_info`."""

    __tablename__ = "inventory_task_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    task_name: str = Field(default="", max_length=255)
    task_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    robot_sn: str = Field(default="", max_length=255)
    task_status: str = Field(default="", max_length=1)
    task_api_url: Optional[str] = Field(default=None, max_length=255)
    map_id: Optional[str] = Field(default=None, max_length=255)
    map_name: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class InventoryTaskStepsEntity(SQLModel, table=True):
    """Inventory task steps — maps to `inventory_task_steps`."""

    __tablename__ = "inventory_task_steps"

    id: str = Field(primary_key=True, max_length=20)
    inventory_task_id: str = Field(default="", max_length=20)
    steps: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class InventoryTaskResultsEntity(SQLModel, table=True):
    """Inventory task results — maps to `inventory_task_results`."""

    __tablename__ = "inventory_task_results"

    id: str = Field(primary_key=True, max_length=20)
    inventory_task_id: str = Field(default="", max_length=20)
    task_results: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Log Extract
# ═══════════════════════════════════════════════════════════════════════


class LogExtractResultEntity(SQLModel, table=True):
    """Log extraction result — maps to `log_extract_result`."""

    __tablename__ = "log_extract_result"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    request_id: Optional[str] = Field(default=None, max_length=50)
    robot_id: Optional[str] = Field(default=None, max_length=40)
    result_url: Optional[str] = Field(default=None, max_length=500)
    create_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Synergy
# ═══════════════════════════════════════════════════════════════════════


class SynergyInfoEntity(SQLModel, table=True):
    """Synergy info — maps to `synergy_info`."""

    __tablename__ = "synergy_info"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    synergy_name: Optional[str] = Field(default=None, max_length=255)
    synergy_type: Optional[str] = Field(default=None, max_length=50)
    synergy_data: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


class Synergy2InfoEntity(SQLModel, table=True):
    """Synergy 2 info — maps to `synergy2_info`."""

    __tablename__ = "synergy2_info"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=20)
    synergy_name: Optional[str] = Field(default=None, max_length=255)
    synergy_type: Optional[str] = Field(default=None, max_length=50)
    synergy_data: Optional[str] = Field(default=None, max_length=65535)
    create_time: Optional[datetime] = Field(default=None)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Agent
# ═══════════════════════════════════════════════════════════════════════


class AgentInfoEntity(SQLModel, table=True):
    """Dify agent info — maps to `agent_info`."""

    __tablename__ = "agent_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    dify_agent_id: str = Field(default="", max_length=64)
    agent_icon: str = Field(default="", max_length=255)
    agent_device_type: str = Field(default="agent", max_length=50)
    agent_name: str = Field(default="", max_length=255)
    agent_description: Optional[str] = Field(default=None, max_length=255)
    copyright: Optional[str] = Field(default=None, max_length=255)
    privacy_policy: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    position: Optional[int] = Field(default=None)
    install_count: Optional[int] = Field(default=None)
    custom_disclaimer: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class RecommendedAgentInfoEntity(SQLModel, table=True):
    """Recommended agent — maps to `recommended_agent_info`."""

    __tablename__ = "recommended_agent_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    dify_agent_id: str = Field(default="", max_length=64)
    dify_recom_app_id: str = Field(default="", max_length=64)
    agent_icon: str = Field(default="", max_length=255)
    agent_device_type: str = Field(default="agent", max_length=50)
    agent_name: str = Field(default="", max_length=255)
    agent_description: Optional[str] = Field(default=None, max_length=255)
    copyright: Optional[str] = Field(default=None, max_length=255)
    privacy_policy: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    position: Optional[int] = Field(default=None)
    install_count: Optional[int] = Field(default=None)
    custom_disclaimer: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════
# Library Entities (Action, Expression, Voice, Knowledge)
# ═══════════════════════════════════════════════════════════════════════


class ActionLibraryInfoEntity(SQLModel, table=True):
    """Action library — maps to `action_library_info`."""

    __tablename__ = "action_library_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    action_library_name: str = Field(default="", max_length=255)
    action_library_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    action_info: Optional[str] = Field(default=None, max_length=65535)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class ExpressionLibraryInfoEntity(SQLModel, table=True):
    """Expression library — maps to `expression_library_info`."""

    __tablename__ = "expression_library_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    expression_library_name: str = Field(default="", max_length=255)
    expression_library_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    expression_info: Optional[str] = Field(default=None, max_length=65535)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class VoiceLibraryInfoEntity(SQLModel, table=True):
    """Voice library — maps to `voice_library_info`."""

    __tablename__ = "voice_library_info"

    id: str = Field(primary_key=True, max_length=20)
    enterprise_id: str = Field(default="", max_length=20)
    voice_library_name: str = Field(default="", max_length=255)
    voice_library_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    voice_info: Optional[str] = Field(default=None, max_length=65535)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)


class KnowledgeLibraryInfoEntity(SQLModel, table=True):
    """Knowledge library — maps to `knowledge_library_info`."""

    __tablename__ = "knowledge_library_info"

    id: str = Field(primary_key=True, max_length=50)
    enterprise_id: str = Field(default="", max_length=20)
    knowledge_library_name: str = Field(default="", max_length=255)
    knowledge_library_description: Optional[str] = Field(default=None, max_length=255)
    robot_type: str = Field(default="", max_length=255)
    document_info: Optional[str] = Field(default=None, max_length=65535)
    dify_knowledge_base_id: Optional[str] = Field(default=None, max_length=255)
    del_flag: Optional[str] = Field(default="1", max_length=1)
    create_by: str = Field(default="", max_length=64)
    creator_id: str = Field(default="", max_length=20)
    create_time: Optional[datetime] = Field(default=None)
    update_by: Optional[str] = Field(default=None, max_length=64)
    updater_id: Optional[str] = Field(default=None, max_length=20)
    update_time: Optional[datetime] = Field(default=None)
