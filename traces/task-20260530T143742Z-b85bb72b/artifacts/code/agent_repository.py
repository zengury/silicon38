"""
SQLModel-backed AgentRepository implementation.
"""
from typing import List, Optional, Dict, Any

from sqlmodel import select

from infrastructure.db.entities import AgentInfoEntity
from ports.repositories import AgentRepository
from .base_repository import BaseCRUDRepository


class SQLAgentRepository(BaseCRUDRepository[AgentInfoEntity], AgentRepository):
    _entity_class = AgentInfoEntity

    def find_recommended_by_dify_id(
        self, dify_agent_id: str
    ) -> List[AgentInfoEntity]:
        with self._session() as session:
            stmt = select(AgentInfoEntity).where(
                AgentInfoEntity.dify_agent_id == dify_agent_id,
                AgentInfoEntity.del_flag == "1",
            )
            return list(session.exec(stmt).all())
