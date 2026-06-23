"""
SQLModel-backed MenuRepository implementation.
"""
from typing import Dict, List, Any, Optional

from sqlmodel import Session, select

from infrastructure.db.connection import engine
from infrastructure.db.entities import (
    SystemMenuEntity,
    SystemRoleMenuEntity,
    SystemUserRoleEntity,
    SystemRoleEntity,
)
from ports.repositories import MenuRepository
from .base_repository import BaseCRUDRepository


class SQLMenuRepository(BaseCRUDRepository[SystemMenuEntity], MenuRepository):
    _entity_class = SystemMenuEntity

    def find_user_menus(
        self, user_id: str, enterprise_id: str, with_perms: bool = True
    ) -> List[SystemMenuEntity]:
        with self._session() as session:
            stmt = (
                select(SystemMenuEntity)
                .join(
                    SystemRoleMenuEntity,
                    SystemMenuEntity.id == SystemRoleMenuEntity.menu_id,
                )
                .join(
                    SystemRoleEntity,
                    SystemRoleMenuEntity.role_id == SystemRoleEntity.id,
                )
                .join(
                    SystemUserRoleEntity,
                    SystemRoleEntity.id == SystemUserRoleEntity.role_id,
                )
                .where(
                    SystemUserRoleEntity.user_id == user_id,
                    SystemMenuEntity.status == "1",
                    SystemMenuEntity.del_flag == "1",
                )
                .distinct()
                .order_by(SystemMenuEntity.order_num)
            )
            menus = list(session.exec(stmt).all())
            return menus

    def find_user_roles(
        self, user_id: str, enterprise_id: str
    ) -> List[SystemRoleEntity]:
        with self._session() as session:
            stmt = (
                select(SystemRoleEntity)
                .join(
                    SystemUserRoleEntity,
                    SystemRoleEntity.id == SystemUserRoleEntity.role_id,
                )
                .where(
                    SystemUserRoleEntity.user_id == user_id,
                    SystemRoleEntity.del_flag == "1",
                )
            )
            return list(session.exec(stmt).all())

    def find_user_perms(
        self, user_id: str, enterprise_id: str
    ) -> List[str]:
        with self._session() as session:
            stmt = (
                select(SystemMenuEntity.perms)
                .join(
                    SystemRoleMenuEntity,
                    SystemMenuEntity.id == SystemRoleMenuEntity.menu_id,
                )
                .join(
                    SystemRoleEntity,
                    SystemRoleMenuEntity.role_id == SystemRoleEntity.id,
                )
                .join(
                    SystemUserRoleEntity,
                    SystemRoleEntity.id == SystemUserRoleEntity.role_id,
                )
                .where(
                    SystemUserRoleEntity.user_id == user_id,
                    SystemMenuEntity.perms.isnot(None),
                    SystemMenuEntity.perms != "",
                    SystemMenuEntity.del_flag == "1",
                )
                .distinct()
            )
            return [p for p in session.exec(stmt).all() if p]

    def find_children(self, parent_id: str) -> List[SystemMenuEntity]:
        with self._session() as session:
            stmt = (
                select(SystemMenuEntity)
                .where(
                    SystemMenuEntity.parent_id == parent_id,
                    SystemMenuEntity.del_flag == "1",
                )
                .order_by(SystemMenuEntity.order_num)
            )
            return list(session.exec(stmt).all())

    def get_options(self, only_parent: bool = False) -> List[Dict[str, Any]]:
        with self._session() as session:
            stmt = select(SystemMenuEntity).where(
                SystemMenuEntity.del_flag == "1",
                SystemMenuEntity.status == "1",
            )
            if only_parent:
                stmt = stmt.where(
                    SystemMenuEntity.parent_id == "0"
                )
            menus = list(session.exec(stmt).all())
            return [
                {
                    "value": m.id,
                    "label": m.menu_name or m.menu_title or "",
                    "children": [] if only_parent else None,
                }
                for m in menus
            ]
