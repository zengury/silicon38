"""Dependency injection container — maps ports to concrete implementations.

Services access repositories through `container.user_repository`,
`container.robot_repository`, etc.  These are lazy-loaded singleton
instances.  For tests, inject mock repositories via the setter methods.
"""

from typing import Optional

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
from db.repositories.user_repository import SQLUserRepository
from db.repositories.robot_repository import SQLRobotRepository
from db.repositories.role_repository import SQLRoleRepository
from db.repositories.menu_repository import SQLMenuRepository
from db.repositories.captcha_repository import SQLCaptchaRepository
from db.repositories.dict_repository import SQLDictRepository
from db.repositories.task_repository import (
    SQLTaskRepository,
    SQLTaskDetailRepository,
    SQLTaskResultRepository,
)
from db.repositories.agent_repository import SQLAgentRepository


class Container:
    """IoC container with lazy-loaded repository singletons.

    Each property returns the real SQLModel-backed implementation on first
    access.  The setter methods allow test code to inject mocks.
    """

    _user_repo: Optional[UserRepository] = None
    _robot_repo: Optional[RobotRepository] = None
    _role_repo: Optional[RoleRepository] = None
    _menu_repo: Optional[MenuRepository] = None
    _captcha_repo: Optional[CaptchaRepository] = None
    _dict_repo: Optional[DictRepository] = None
    _task_repo: Optional[TaskRepository] = None
    _task_detail_repo: Optional[TaskDetailRepository] = None
    _task_result_repo: Optional[TaskResultRepository] = None
    _agent_repo: Optional[AgentRepository] = None

    @property
    def user_repository(self) -> UserRepository:
        if self._user_repo is None:
            self._user_repo = SQLUserRepository()
        return self._user_repo

    @user_repository.setter
    def user_repository(self, repo: UserRepository) -> None:
        self._user_repo = repo

    @property
    def robot_repository(self) -> RobotRepository:
        if self._robot_repo is None:
            self._robot_repo = SQLRobotRepository()
        return self._robot_repo

    @robot_repository.setter
    def robot_repository(self, repo: RobotRepository) -> None:
        self._robot_repo = repo

    @property
    def role_repository(self) -> RoleRepository:
        if self._role_repo is None:
            self._role_repo = SQLRoleRepository()
        return self._role_repo

    @role_repository.setter
    def role_repository(self, repo: RoleRepository) -> None:
        self._role_repo = repo

    @property
    def menu_repository(self) -> MenuRepository:
        if self._menu_repo is None:
            self._menu_repo = SQLMenuRepository()
        return self._menu_repo

    @menu_repository.setter
    def menu_repository(self, repo: MenuRepository) -> None:
        self._menu_repo = repo

    @property
    def captcha_repository(self) -> CaptchaRepository:
        if self._captcha_repo is None:
            self._captcha_repo = SQLCaptchaRepository()
        return self._captcha_repo

    @captcha_repository.setter
    def captcha_repository(self, repo: CaptchaRepository) -> None:
        self._captcha_repo = repo

    @property
    def dict_repository(self) -> DictRepository:
        if self._dict_repo is None:
            self._dict_repo = SQLDictRepository()
        return self._dict_repo

    @dict_repository.setter
    def dict_repository(self, repo: DictRepository) -> None:
        self._dict_repo = repo

    @property
    def task_repository(self) -> TaskRepository:
        if self._task_repo is None:
            self._task_repo = SQLTaskRepository()
        return self._task_repo

    @task_repository.setter
    def task_repository(self, repo: TaskRepository) -> None:
        self._task_repo = repo

    @property
    def task_detail_repository(self) -> TaskDetailRepository:
        if self._task_detail_repo is None:
            self._task_detail_repo = SQLTaskDetailRepository()
        return self._task_detail_repo

    @task_detail_repository.setter
    def task_detail_repository(self, repo: TaskDetailRepository) -> None:
        self._task_detail_repo = repo

    @property
    def task_result_repository(self) -> TaskResultRepository:
        if self._task_result_repo is None:
            self._task_result_repo = SQLTaskResultRepository()
        return self._task_result_repo

    @task_result_repository.setter
    def task_result_repository(self, repo: TaskResultRepository) -> None:
        self._task_result_repo = repo

    @property
    def agent_repository(self) -> AgentRepository:
        if self._agent_repo is None:
            self._agent_repo = SQLAgentRepository()
        return self._agent_repo

    @agent_repository.setter
    def agent_repository(self, repo: AgentRepository) -> None:
        self._agent_repo = repo


# Module-level singleton — import this everywhere
container = Container()
