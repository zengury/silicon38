"""
SQLModel-backed CaptchaRepository implementation.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select, delete

from infrastructure.db.connection import engine
from infrastructure.db.entities import CaptchaEntity
from ports.repositories import CaptchaRepository
from .base_repository import BaseCRUDRepository


class SQLCaptchaRepository(
    BaseCRUDRepository[CaptchaEntity], CaptchaRepository
):
    _entity_class = CaptchaEntity

    def find_by_key(self, captcha_key: str) -> Optional[CaptchaEntity]:
        with self._session() as session:
            stmt = select(CaptchaEntity).where(
                CaptchaEntity.captcha_key == captcha_key
            )
            return session.exec(stmt).first()

    def delete_expired(self) -> None:
        with self._session() as session:
            session.exec(
                delete(CaptchaEntity).where(
                    CaptchaEntity.expire_time < datetime.now()
                )
            )
            session.commit()
