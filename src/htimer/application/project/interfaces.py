from abc import abstractmethod
from typing import Protocol

from htimer.domain import entities

from . import exceptions


class ProjectAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_project(
        self, actor: entities.User
    ) -> exceptions.ProjectAuthorizationError | None:
        pass

    @abstractmethod
    def decide_update_project(
        self,
        actor: entities.User,
        project: entities.Project,
        members: list[entities.User],
    ) -> exceptions.ProjectAuthorizationError | None:
        pass

    @abstractmethod
    def decide_get_project(
        self,
        actor: entities.User,
        project: entities.Project,
        members: list[entities.User],
    ) -> exceptions.ProjectAuthorizationError | None:
        pass
