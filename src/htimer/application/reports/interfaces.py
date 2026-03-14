from abc import abstractmethod
from typing import Any, Protocol

from htimer.domain import entities

from . import exceptions

type ContentType = dict[str, Any | ContentType]


class ReportsAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_report(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
        target_users: list[entities.User] | None,
    ) -> exceptions.ReportAuthorizationError | None:
        pass


class ReportVizualizer(Protocol):
    @abstractmethod
    def vizualize(self, content: ContentType) -> bytes:
        pass
