"""
Unit tests for di.container — DI wiring and test injection.
"""

import pytest
from unittest.mock import MagicMock

from di.container import Container
from ports.repositories import (
    UserRepository,
    RobotRepository,
    RoleRepository,
    MenuRepository,
    CaptchaRepository,
    DictRepository,
    TaskRepository,
    TaskDetailRepository,
    TaskResultRepository,
    AgentRepository,
)


class TestContainer:
    """Verify DI container lazy-loads and supports injection."""

    def test_user_repository_lazy(self):
        c = Container()
        repo = c.user_repository
        assert repo is not None
        # Same one on second access
        assert c.user_repository is repo

    def test_robot_repository_lazy(self):
        c = Container()
        assert c.robot_repository is not None

    def test_role_repository_lazy(self):
        c = Container()
        assert c.role_repository is not None

    def test_menu_repository_lazy(self):
        c = Container()
        assert c.menu_repository is not None

    def test_captcha_repository_lazy(self):
        c = Container()
        assert c.captcha_repository is not None

    def test_dict_repository_lazy(self):
        c = Container()
        assert c.dict_repository is not None

    def test_task_repositories_lazy(self):
        c = Container()
        assert c.task_repository is not None
        assert c.task_detail_repository is not None
        assert c.task_result_repository is not None

    def test_agent_repository_lazy(self):
        c = Container()
        assert c.agent_repository is not None

    def test_injection_setter(self):
        c = Container()
        mock_repo = MagicMock(spec=UserRepository)
        c.user_repository = mock_repo
        assert c.user_repository is mock_repo

    def test_multiple_injections(self):
        c = Container()
        mock_user = MagicMock(spec=UserRepository)
        mock_robot = MagicMock(spec=RobotRepository)
        c.user_repository = mock_user
        c.robot_repository = mock_robot
        assert c.user_repository is mock_user
        assert c.robot_repository is mock_robot

    def test_global_singleton(self):
        from di.container import container as g1
        from di.container import container as g2
        assert g1 is g2

    def test_all_repos_different_instances(self):
        c = Container()
        repos = [
            c.user_repository,
            c.robot_repository,
            c.role_repository,
            c.menu_repository,
        ]
        # Each repo should be a distinct instance
        for i in range(len(repos)):
            for j in range(i + 1, len(repos)):
                assert repos[i] is not repos[j]
