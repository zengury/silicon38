"""
SQLModel-backed RobotRepository implementation.
"""
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select

from infrastructure.db.connection import engine
from infrastructure.db.entities import RobotEntity
from ports.repositories import RobotRepository
from .base_repository import BaseCRUDRepository


class SQLRobotRepository(BaseCRUDRepository[RobotEntity], RobotRepository):
    _entity_class = RobotEntity

    def find_by_serial_no(self, serial_no: str) -> Optional[RobotEntity]:
        with self._session() as session:
            stmt = select(RobotEntity).where(RobotEntity.serial_no == serial_no)
            return session.exec(stmt).first()

    def page(self, page_no: int, page_size: int) -> Dict[str, Any]:
        return self.search([], page_no, page_size)

    def get_list(self) -> List[RobotEntity]:
        with self._session() as session:
            stmt = select(RobotEntity).where(RobotEntity.del_flag == "1")
            return list(session.exec(stmt).all())
