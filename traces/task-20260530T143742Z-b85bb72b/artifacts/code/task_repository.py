"""
SQLModel-backed TaskRepository, TaskDetailRepository, TaskResultRepository.
"""
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, delete

from infrastructure.db.connection import engine
from infrastructure.db.entities import (
    TaskInfoEntity,
    TaskInfoDetailEntity,
    TaskResultDetailEntity,
)
from ports.repositories import (
    TaskRepository,
    TaskDetailRepository,
    TaskResultRepository,
)
from .base_repository import BaseCRUDRepository


class SQLTaskRepository(BaseCRUDRepository[TaskInfoEntity], TaskRepository):
    _entity_class = TaskInfoEntity


class SQLTaskDetailRepository(
    BaseCRUDRepository[TaskInfoDetailEntity], TaskDetailRepository
):
    _entity_class = TaskInfoDetailEntity

    def find_by_task_id(self, task_id: str) -> List[TaskInfoDetailEntity]:
        with self._session() as session:
            stmt = select(TaskInfoDetailEntity).where(
                TaskInfoDetailEntity.task_id == task_id
            )
            return list(session.exec(stmt).all())

    def delete_by_task_id(self, task_id: str) -> None:
        with self._session() as session:
            session.exec(
                delete(TaskInfoDetailEntity).where(
                    TaskInfoDetailEntity.task_id == task_id
                )
            )
            session.commit()


class SQLTaskResultRepository(
    BaseCRUDRepository[TaskResultDetailEntity], TaskResultRepository
):
    _entity_class = TaskResultDetailEntity

    def find_by_task_id(self, task_id: str) -> List[TaskResultDetailEntity]:
        with self._session() as session:
            stmt = select(TaskResultDetailEntity).where(
                TaskResultDetailEntity.task_id == task_id
            )
            return list(session.exec(stmt).all())

    def delete_by_task_id(self, task_id: str) -> None:
        with self._session() as session:
            session.exec(
                delete(TaskResultDetailEntity).where(
                    TaskResultDetailEntity.task_id == task_id
                )
            )
            session.commit()
