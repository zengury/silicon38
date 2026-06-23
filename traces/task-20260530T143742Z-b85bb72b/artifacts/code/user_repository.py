"""
SQLModel-backed UserRepository implementation.

Thin bridge between the UserRepository port and SQLModel Session.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete
from loguru import logger

from infrastructure.db.connection import engine
from infrastructure.db.entities import (
    UserEntity,
    SystemRoleEntity,
    SystemUserRoleEntity,
)
from ports.repositories import UserRepository
from .base_repository import BaseCRUDRepository


class SQLUserRepository(BaseCRUDRepository[UserEntity], UserRepository):
    _entity_class = UserEntity

    def find_by_username(self, username: str) -> Optional[UserEntity]:
        with self._session() as session:
            stmt = select(UserEntity).where(UserEntity.username == username)
            return session.exec(stmt).first()

    def find_by_email(self, email: str) -> Optional[UserEntity]:
        with self._session() as session:
            stmt = select(UserEntity).where(UserEntity.email == email)
            return session.exec(stmt).first()

    def find_by_mobile(self, mobile: str) -> Optional[UserEntity]:
        with self._session() as session:
            stmt = select(UserEntity).where(UserEntity.mobile == mobile)
            return session.exec(stmt).first()

    def find_by_username_or_email_or_mobile(
        self, value: str
    ) -> Optional[UserEntity]:
        with self._session() as session:
            from sqlalchemy import or_
            stmt = select(UserEntity).where(
                or_(
                    UserEntity.username == value,
                    UserEntity.email == value,
                    UserEntity.mobile == value,
                )
            )
            return session.exec(stmt).first()

    def update_password(self, user_id: str, password_hash: str) -> UserEntity:
        return self.update_field(user_id, "password", password_hash)

    def find_user_roles(self, user_id: str) -> List[Any]:
        with self._session() as session:
            stmt = (
                select(SystemRoleEntity)
                .join(
                    SystemUserRoleEntity,
                    SystemRoleEntity.id == SystemUserRoleEntity.role_id,
                )
                .where(SystemUserRoleEntity.user_id == user_id)
            )
            return list(session.exec(stmt).all())

    def set_user_roles(
        self,
        enterprise_id: str,
        user_id: str,
        role_ids: List[str],
    ) -> None:
        with self._session() as session:
            # Remove existing roles
            session.exec(
                delete(SystemUserRoleEntity).where(
                    SystemUserRoleEntity.user_id == user_id
                )
            )
            # Add new roles
            from common import IdUtil
            now = datetime.now()
            for role_id in role_ids:
                ur = SystemUserRoleEntity(
                    id=str(IdUtil.get_next_id()),
                    user_id=user_id,
                    role_id=role_id,
                )
                session.add(ur)
            session.commit()
