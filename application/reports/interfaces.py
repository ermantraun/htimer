from typing import Protocol
from abc import abstractmethod
from domain import entities
from . import exceptions

class ReportsAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_report(self, actor: entities.User, project: entities.Project, project_members: list[entities.User], target_users: list[entities.User]) -> exceptions.ReportAuthorizationError | None:
        pass
