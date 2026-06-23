"""
SQLModel-backed DictRepository implementation.
"""
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select

from infrastructure.db.connection import engine
from infrastructure.db.entities import DictEntity, DictItemEntity
from ports.repositories import DictRepository
from .base_repository import BaseCRUDRepository


class SQLDictRepository(BaseCRUDRepository[DictEntity], DictRepository):
    _entity_class = DictEntity

    def save_item(self, entity: DictItemEntity) -> DictItemEntity:
        with self._session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def update_item(self, entity: DictItemEntity) -> DictItemEntity:
        with self._session() as session:
            session.merge(entity)
            session.commit()
            return entity

    def delete_items(self, ids: List[str]) -> None:
        with self._session() as session:
            stmt = select(DictItemEntity).where(DictItemEntity.id.in_(ids))
            items = session.exec(stmt).all()
            for item in items:
                session.delete(item)
            session.commit()

    def search_items(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        with self._session() as session:
            base = select(DictItemEntity)
            for f in filters or []:
                field_name = f.get("field_name")
                operator = f.get("operator", "eq")
                value = f.get("value")
                if field_name and hasattr(DictItemEntity, field_name):
                    column = getattr(DictItemEntity, field_name)
                    if operator == "eq":
                        base = base.where(column == value)
                    elif operator == "like":
                        base = base.where(column.like(f"%{value}%"))

            total = len(session.exec(base).all())
            offset = (page_no - 1) * page_size
            stmt = base.offset(offset).limit(page_size)
            items = list(session.exec(stmt).all())
            return {"total": total, "items": items}

    def find_items_by_dict_code(self, dict_code: str) -> List[DictItemEntity]:
        with self._session() as session:
            dict_stmt = select(DictEntity).where(
                DictEntity.dict_code == dict_code
            )
            dict_entity = session.exec(dict_stmt).first()
            if not dict_entity:
                return []
            stmt = select(DictItemEntity).where(
                DictItemEntity.dict_id == dict_entity.id,
                DictItemEntity.status == 1,
            )
            return list(session.exec(stmt).all())
