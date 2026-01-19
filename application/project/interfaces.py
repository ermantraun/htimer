from abc import abstractmethod
from typing import Protocol
from domain import entities
import exceptions

class ProjectCreateAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_project(self, actor: entities.User) -> exceptions.ProjectAuthorizationError | None:
        pass

class ProjectUpdateAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_update_project(self, actor: entities.User, project: entities.Project, members: list[entities.User]) -> exceptions.ProjectAuthorizationError | None:
        pass

class ProjectGetterAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_get_project(self, actor: entities.User, project: entities.Project, members: list[entities.User]) -> exceptions.ProjectAuthorizationError | None:
        pass
