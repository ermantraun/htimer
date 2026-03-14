from dataclasses import dataclass
from uuid import UUID

from htimer.domain import entities


@dataclass
class CreateProjectInDTO:
    name: str
    description: str | None
    start_date: str | None = None
    end_date: str | None = None


@dataclass
class CreateProjectOutDTO:
    project: entities.Project


@dataclass
class UpdateProjectInDTO:
    uuid: UUID
    name: str | None = None
    description: str | None = None
    status: entities.ProjectStatus | None = None
    start_date: str | None = None
    end_date: str | None = None


@dataclass
class UpdateProjectOutDTO:
    project: entities.Project


@dataclass
class GetProjectInDTO:
    project_uuid: UUID


@dataclass
class GetProjectsOutDTO:
    project: entities.Project
    members: list[entities.User]


@dataclass
class AddMembersInDTO:
    project_uuid: UUID
    members_uuids: list[UUID]


@dataclass
class AddMembersOutDTO:
    members: list[entities.MemberShip]


@dataclass
class RemoveMembersInDTO:
    project_uuid: UUID
    members_uuids: list[UUID]


@dataclass
class RemoveMembersOutDTO:
    project: entities.Project


@dataclass
class GetProjectListInDTO:
    # no fields for now; reserved for future filters
    pass


@dataclass
class GetProjectListOutDTO:
    projects: list[entities.Project]
