"""
Base CRUD repository with reusable SQLModel Session operations.

All concrete repositories extend this with entity-specific query logic.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, select, func
from loguru import logger

from infrastructure.db.connection import engine

E = TypeVar("E")


class BaseCRUDRepository(Generic[E]):
    """Generic CRUD operations for a single entity type.

    Can be used in two ways:
    1. Subclass and set `_entity_class` (port/adapter pattern).
    2. Instantiate directly with `BaseCRUDRepository(MyEntity)` for simple CRUD.
    """

    _entity_class: Type[E]

    def __init__(self, entity_class: Type[E] = None) -> None:
        """Optionally accept entity_class for direct instantiation.

        If `entity_class` is provided, it overrides the class-level
        `_entity_class` so that services can use BaseCRUDRepository(Entity)
        without creating a named subclass.
        """
        if entity_class is not None:
            self._entity_class = entity_class

    def _session(self) -> Session:
        """Return a new SQLModel Session bound to the global engine.

        This is a convenience method.  For transactional boundaries across
        multiple entities, use a single Session context manager directly.
        """
        return Session(engine)

    # ── Create / Update ────────────────────────────────────────────────

    def save(self, entity: E) -> E:
        with self._session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def update(self, entity: E) -> E:
        with self._session() as session:
            session.merge(entity)
            session.commit()
            return entity

    # ── Read ───────────────────────────────────────────────────────────

    def find_by_id(self, entity_id: str) -> Optional[E]:
        with self._session() as session:
            stmt = select(self._entity_class).where(
                getattr(self._entity_class, "id") == entity_id
            )
            return session.exec(stmt).first()

    def find_all(self) -> List[E]:
        with self._session() as session:
            stmt = select(self._entity_class)
            return list(session.exec(stmt).all())

    # ── Delete ─────────────────────────────────────────────────────────

    def soft_delete(self, entity_id: str) -> None:
        """Set del_flag to '0' (soft-delete convention for most entities)."""
        with self._session() as session:
            stmt = select(self._entity_class).where(
                getattr(self._entity_class, "id") == entity_id
            )
            entity = session.exec(stmt).first()
            if entity and hasattr(entity, "del_flag"):
                entity.del_flag = "0"
                session.add(entity)
                session.commit()

    def hard_delete(self, entity_id: str) -> None:
        """Physically remove the entity (use sparingly)."""
        with self._session() as session:
            stmt = select(self._entity_class).where(
                getattr(self._entity_class, "id") == entity_id
            )
            entity = session.exec(stmt).first()
            if entity:
                session.delete(entity)
                session.commit()

    def delete_by_ids(self, ids: List[str]) -> None:
        """Soft-delete multiple entities by ID list."""
        with self._session() as session:
            stmt = select(self._entity_class).where(
                getattr(self._entity_class, "id").in_(ids)
            )
            entities = session.exec(stmt).all()
            for entity in entities:
                if hasattr(entity, "del_flag"):
                    entity.del_flag = "0"
                    session.add(entity)
            session.commit()

    # ── Search / Paginate ──────────────────────────────────────────────

    def _apply_filters(self, stmt, filters: List[Dict[str, Any]]):
        """Apply dynamic filters to a select statement.

        Each filter is a dict with: field_name, operator, value.
        Supported operators: eq, ne, like, gt, lt, gte, lte, in.
        """
        for f in filters or []:
            field_name = f.get("field_name")
            operator = f.get("operator", "eq")
            value = f.get("value")
            if not field_name or not hasattr(self._entity_class, field_name):
                continue
            column = getattr(self._entity_class, field_name)
            if operator == "eq":
                stmt = stmt.where(column == value)
            elif operator == "ne":
                stmt = stmt.where(column != value)
            elif operator == "like":
                stmt = stmt.where(column.like(f"%{value}%"))
            elif operator == "gt":
                stmt = stmt.where(column > value)
            elif operator == "lt":
                stmt = stmt.where(column < value)
            elif operator == "gte":
                stmt = stmt.where(column >= value)
            elif operator == "lte":
                stmt = stmt.where(column <= value)
            elif operator == "in" and value:
                stmt = stmt.where(column.in_(value))
        return stmt

    def search(
        self, filters: List[Dict[str, Any]], page_no: int, page_size: int
    ) -> Dict[str, Any]:
        """Paginated search with dynamic filters.

        Returns {"total": int, "items": List[E]}.
        """
        with self._session() as session:
            base = select(self._entity_class)
            base = self._apply_filters(base, filters)

            # Only soft-delete filter if entity has del_flag
            if hasattr(self._entity_class, "del_flag"):
                base = base.where(self._entity_class.del_flag == "1")

            total = len(session.exec(base).all())
            offset = (page_no - 1) * page_size
            stmt = base.offset(offset).limit(page_size)
            items = list(session.exec(stmt).all())
            return {"total": total, "items": items}

    def update_field(self, entity_id: str, field_name: str, value: Any) -> Any:
        """Update a single field on an entity by ID."""
        with self._session() as session:
            stmt = select(self._entity_class).where(
                getattr(self._entity_class, "id") == entity_id
            )
            entity = session.exec(stmt).first()
            if entity and hasattr(entity, field_name):
                setattr(entity, field_name, value)
                session.add(entity)
                session.commit()
                session.refresh(entity)
            return entity
