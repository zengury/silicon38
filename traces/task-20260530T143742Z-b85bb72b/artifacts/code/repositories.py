"""
Repository ports — abstract interfaces for data access.

Domain services depend on these ABCs, never on concrete SQLModel Session
or engine directly.  Concrete implementations live in db/repositories/.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from infrastructure.db.entities import (
    UserEntity,
    SystemRoleEntity,
    SystemMenuEntity,
    RobotEntity,
    CaptchaEntity,
    DictEntity,
    DictItemEntity,
    TaskInfoEntity,
    TaskInfoDetailEntity,
    TaskResultDetailEntity,
    AgentInfoEntity,
)


# ═══════════════════════════════════════════════════════════════════════
# User Repository
# ═══════════════════════════════════════════════════════════════════════


class UserRepository(ABC):
    """Abstract repository for UserEntity CRUD and queries."""

    @abstractmethod
    def save(self, entity: UserEntity) -> UserEntity:
        """Create or update a user."""
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[UserEntity]:
        """Find a user by primary key."""
        ...

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[UserEntity]:
        """Find a user by exact username match."""
        ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[UserEntity]:
        """Find a user by exact email match."""
        ...

    @abstractmethod
    def find_by_mobile(self, mobile: str) -> Optional[UserEntity]:
        """Find a user by exact mobile match."""
        ...

    @abstractmethod
    def find_by_username_or_email_or_mobile(
        self, value: str
    ) -> Optional[UserEntity]:
        """Find a user by username, email, or mobile (OR match)."""
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        """Paginated user search with dynamic filters.

        Returns {"total": int, "items": List[UserEntity]}.
        """
        ...

    @abstractmethod
    def update(self, entity: UserEntity) -> UserEntity:
        """Update all fields of an existing user."""
        ...

    @abstractmethod
    def update_field(self, user_id: str, field_name: str, value) -> UserEntity:
        """Update a single field by name."""
        ...

    @abstractmethod
    def update_password(self, user_id: str, password_hash: str) -> UserEntity:
        """Update only the password hash."""
        ...

    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """Soft-delete users by ID list."""
        ...

    @abstractmethod
    def set_user_roles(
        self,
        enterprise_id: str,
        user_id: str,
        role_ids: List[str],
    ) -> None:
        """Replace user-role associations."""
        ...

    @abstractmethod
    def find_user_roles(self, user_id: str) -> List[Any]:
        """Return the roles assigned to a user."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Robot Repository
# ═══════════════════════════════════════════════════════════════════════


class RobotRepository(ABC):
    """Abstract repository for RobotEntity CRUD and queries."""

    @abstractmethod
    def save(self, entity: RobotEntity) -> RobotEntity:
        ...

    @abstractmethod
    def find_by_id(self, robot_id: str) -> Optional[RobotEntity]:
        ...

    @abstractmethod
    def find_all(self) -> List[RobotEntity]:
        """Return all non-deleted robots."""
        ...

    @abstractmethod
    def find_by_serial_no(self, serial_no: str) -> Optional[RobotEntity]:
        ...

    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """Soft-delete robots by ID list."""
        ...

    @abstractmethod
    def update(self, entity: RobotEntity) -> RobotEntity:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        """Paginated robot search.

        Returns {"total": int, "items": List[RobotEntity]}.
        """
        ...

    @abstractmethod
    def page(self, page_no: int, page_size: int) -> Dict[str, Any]:
        """Simple paginated list without filters."""
        ...

    @abstractmethod
    def get_list(self) -> List[RobotEntity]:
        """Return all robots as a flat list."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Role Repository
# ═══════════════════════════════════════════════════════════════════════


class RoleRepository(ABC):
    """Abstract repository for SystemRoleEntity CRUD and queries."""

    @abstractmethod
    def find_by_id(self, role_id: str) -> Optional[SystemRoleEntity]:
        ...

    @abstractmethod
    def find_all(self) -> List[SystemRoleEntity]:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def save(self, entity: SystemRoleEntity) -> SystemRoleEntity:
        ...

    @abstractmethod
    def find_by_role_key_and_enterprise(
        self, role_key: str, enterprise_id: str
    ) -> Optional[SystemRoleEntity]:
        ...

    @abstractmethod
    def find_menu_ids(self, role_id: str) -> List[str]:
        """Return menu IDs assigned to a role."""
        ...

    @abstractmethod
    def soft_delete(self, role_id: str) -> None:
        ...

    @abstractmethod
    def replace_menu_ids(
        self, role_id: str, menu_ids: List[str], enterprise_id: str
    ) -> None:
        """Replace role-menu associations."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Menu Repository
# ═══════════════════════════════════════════════════════════════════════


class MenuRepository(ABC):
    """Abstract repository for SystemMenuEntity queries and tree building."""

    @abstractmethod
    def find_all(self) -> List[SystemMenuEntity]:
        ...

    @abstractmethod
    def find_by_id(self, menu_id: str) -> Optional[SystemMenuEntity]:
        ...

    @abstractmethod
    def save(self, entity: SystemMenuEntity) -> SystemMenuEntity:
        ...

    @abstractmethod
    def update(self, entity: SystemMenuEntity) -> SystemMenuEntity:
        ...

    @abstractmethod
    def soft_delete(self, menu_id: str) -> None:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def find_user_menus(
        self, user_id: str, enterprise_id: str, with_perms: bool
    ) -> List[SystemMenuEntity]:
        """Return all menus accessible to a user (with permissions)."""
        ...

    @abstractmethod
    def find_user_roles(
        self, user_id: str, enterprise_id: str
    ) -> List[SystemRoleEntity]:
        """Return roles assigned to a user."""
        ...

    @abstractmethod
    def find_user_perms(
        self, user_id: str, enterprise_id: str
    ) -> List[str]:
        """Return permission strings for a user."""
        ...

    @abstractmethod
    def find_children(self, parent_id: str) -> List[SystemMenuEntity]:
        """Return child menus of a parent."""
        ...

    @abstractmethod
    def get_options(self, only_parent: bool = False) -> List[Dict[str, Any]]:
        """Return menu tree as option dicts (for dropdowns)."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Captcha Repository
# ═══════════════════════════════════════════════════════════════════════


class CaptchaRepository(ABC):
    """Abstract repository for CaptchaEntity CRUD."""

    @abstractmethod
    def save(self, entity: CaptchaEntity) -> CaptchaEntity:
        ...

    @abstractmethod
    def find_by_key(self, captcha_key: str) -> Optional[CaptchaEntity]:
        ...

    @abstractmethod
    def delete_expired(self) -> None:
        """Remove expired captcha records."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# Dict Repository
# ═══════════════════════════════════════════════════════════════════════


class DictRepository(ABC):
    """Abstract repository for DictEntity and DictItemEntity CRUD."""

    @abstractmethod
    def save(self, entity: DictEntity) -> DictEntity:
        ...

    @abstractmethod
    def update(self, entity: DictEntity) -> DictEntity:
        ...

    @abstractmethod
    def find_by_id(self, dict_id: str) -> Optional[DictEntity]:
        ...

    @abstractmethod
    def soft_delete(self, dict_id: str) -> None:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def save_item(self, entity: DictItemEntity) -> DictItemEntity:
        ...

    @abstractmethod
    def update_item(self, entity: DictItemEntity) -> DictItemEntity:
        ...

    @abstractmethod
    def delete_items(self, ids: List[str]) -> None:
        ...

    @abstractmethod
    def search_items(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def find_items_by_dict_code(self, dict_code: str) -> List[DictItemEntity]:
        ...


# ═══════════════════════════════════════════════════════════════════════
# Task Repositories
# ═══════════════════════════════════════════════════════════════════════


class TaskRepository(ABC):
    """Abstract repository for TaskInfoEntity CRUD."""

    @abstractmethod
    def save(self, entity: TaskInfoEntity) -> TaskInfoEntity:
        ...

    @abstractmethod
    def update(self, entity: TaskInfoEntity) -> TaskInfoEntity:
        ...

    @abstractmethod
    def find_by_id(self, task_id: str) -> Optional[TaskInfoEntity]:
        ...

    @abstractmethod
    def soft_delete(self, task_id: str) -> None:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def update_field(self, task_id: str, field: str, value: Any) -> None:
        ...


class TaskDetailRepository(ABC):
    """Abstract repository for TaskInfoDetailEntity CRUD."""

    @abstractmethod
    def save(self, entity: TaskInfoDetailEntity) -> TaskInfoDetailEntity:
        ...

    @abstractmethod
    def find_by_task_id(self, task_id: str) -> List[TaskInfoDetailEntity]:
        ...

    @abstractmethod
    def delete_by_task_id(self, task_id: str) -> None:
        ...


class TaskResultRepository(ABC):
    """Abstract repository for TaskResultDetailEntity CRUD."""

    @abstractmethod
    def save(self, entity: TaskResultDetailEntity) -> TaskResultDetailEntity:
        ...

    @abstractmethod
    def find_by_task_id(self, task_id: str) -> List[TaskResultDetailEntity]:
        ...

    @abstractmethod
    def delete_by_task_id(self, task_id: str) -> None:
        ...


# ═══════════════════════════════════════════════════════════════════════
# Agent Repository
# ═══════════════════════════════════════════════════════════════════════


class AgentRepository(ABC):
    """Abstract repository for AgentInfoEntity CRUD."""

    @abstractmethod
    def save(self, entity: AgentInfoEntity) -> AgentInfoEntity:
        ...

    @abstractmethod
    def find_by_id(self, agent_id: str) -> Optional[AgentInfoEntity]:
        ...

    @abstractmethod
    def find_all(self) -> List[AgentInfoEntity]:
        ...

    @abstractmethod
    def soft_delete(self, agent_id: str) -> None:
        ...

    @abstractmethod
    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    def find_recommended_by_dify_id(
        self, dify_agent_id: str
    ) -> List[AgentInfoEntity]:
        """Find recommended agents by Dify agent ID."""
        ...
