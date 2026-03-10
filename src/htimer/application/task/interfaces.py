from typing import Protocol
from abc import abstractmethod
from domain import entities
from . import exceptions

class TaskAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_task(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.TaskAuthorizationError | None:
        pass

    @abstractmethod
    def decide_update_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.TaskAuthorizationError | None:
        pass

    @abstractmethod
    def decide_get_task(self, actor: entities.User, task_project: entities.Project, task_project_members: list[entities.User]) -> exceptions.TaskAuthorizationError | None:
        pass

    @abstractmethod
    def decide_delete_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.TaskAuthorizationError | None:
        pass
