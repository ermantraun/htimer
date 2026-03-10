from typing import Protocol, BinaryIO, Any
from abc import abstractmethod
from domain import entities
from . import exceptions

ContentType = dict[Any, dict[Any, "ContentType"]] | list[dict[Any, Any]]


class ReportsAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_report(self, actor: entities.User, project: entities.Project, project_members: list[entities.User], target_users: list[entities.User] | None) -> exceptions.ReportAuthorizationError | None:
        pass


class ReportVizualizer(Protocol):

    @abstractmethod
    def vizualize(self, content: ContentType) -> bytes:
        pass

    @abstractmethod
    def create_vizualization_file(self, content: bytes) -> BinaryIO:
        pass