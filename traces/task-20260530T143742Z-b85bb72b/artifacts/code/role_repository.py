"""
SQLModel-backed RoleRepository implementation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlmodel import Session, select, delete

from infrastructure.db.connection import engine
from infrastructure.db.entities import (
    SystemRoleEntity,
    SystemRoleMenuEntity,
)
from ports.repositories import RoleRepository
from .base_repository import BaseCRUDRepository


class SQLRoleRepository(BaseCRUDRepository[SystemRoleEntity], RoleRepository):
    _entity_class = SystemRoleEntity

    def find_by_role_key_and_enterprise(
        self, role_key: str, enterprise_id: str
    ) -> Optional[SystemRoleEntity]:
        with self._session() as session:
            stmt = select(SystemRoleEntity).where(
                SystemRoleEntity.role_key == role_key,
                SystemRoleEntity.enterprise_id == enterprise_id,
            )
            return session.exec(stmt).first()

    def find_menu_ids(self, role_id: str) -> List[str]:
        with self._session() as session:
            stmt = select(SystemRoleMenuEntity.menu_id).where(
                SystemRoleMenuEntity.role_id == role_id
            )
            return [row for row in session.exec(stmt).all()]

    def replace_menu_ids(
        self, role_id: str, menu_ids: List[str], enterprise_id: str
    ) -> None:
        with self._session() as session:
            # Remove existing menu assignments
            session.exec(
                delete(SystemRoleMenuEntity).where(
                    SystemRoleMenuEntity.role_id == role_id
                )
            )
            # Add new ones
            from common import IdUtil
            for menu_id in menu_ids:
                rme = SystemRoleMenuEntity(
                    id=str(IdUtil.get_next_id()),
                    role_id=role_id,
                    menu_id=menu_id,
                )
                session.add(rme)
            session.commit()
