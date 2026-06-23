"""
Unit tests for infrastructure.db.entities — entity definitions.
"""

from infrastructure.db.entities import (
    UserEntity,
    RobotEntity,
    SystemMenuEntity,
    SystemRoleEntity,
    TaskInfoEntity,
    AgentInfoEntity,
    ActionLibraryInfoEntity,
    KnowledgeLibraryInfoEntity,
)


class TestEntities:
    """Verify entity table names, primary keys, and class count."""

    def test_user_entity_table(self):
        assert UserEntity.__tablename__ == "user"
        assert "id" in UserEntity.__table__.columns.keys()

    def test_robot_entity_table(self):
        assert RobotEntity.__tablename__ == "robot"
        assert "serial_no" in RobotEntity.__table__.columns.keys()

    def test_system_menu_table(self):
        assert SystemMenuEntity.__tablename__ == "sys_menu"
        assert "menu_name" in SystemMenuEntity.__table__.columns.keys()

    def test_system_role_table(self):
        assert SystemRoleEntity.__tablename__ == "sys_role"
        assert "role_key" in SystemRoleEntity.__table__.columns.keys()

    def test_task_info_table(self):
        assert TaskInfoEntity.__tablename__ == "task_info"
        assert "task_name" in TaskInfoEntity.__table__.columns.keys()

    def test_agent_info_table(self):
        assert AgentInfoEntity.__tablename__ == "agent_info"
        assert "dify_agent_id" in AgentInfoEntity.__table__.columns.keys()

    def test_action_library_table(self):
        assert ActionLibraryInfoEntity.__tablename__ == "action_library_info"
        assert "action_library_name" in ActionLibraryInfoEntity.__table__.columns.keys()

    def test_knowledge_library_table(self):
        assert KnowledgeLibraryInfoEntity.__tablename__ == "knowledge_library_info"

    def test_entity_count(self):
        """Verify at least the core entities are defined."""
        from infrastructure.db import entities as e
        # Count classes with __tablename__ set
        entity_count = sum(
            1
            for name in dir(e)
            if isinstance(getattr(e, name), type)
            and hasattr(getattr(e, name), "__tablename__")
        )
        assert entity_count >= 30, f"Expected >=30 entities, found {entity_count}"
