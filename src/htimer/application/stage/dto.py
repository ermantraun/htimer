from dataclasses import dataclass
from uuid import UUID

from htimer.domain import entities


@dataclass
class CreateStageInDTO:
    name: str
    project_uuid: UUID
    parent_uuid: UUID | None = None
    description: str | None = None
    main_path: bool | None = None


@dataclass
class CreateStageOutDTO:
    stage: entities.Stage


@dataclass
class UpdateStageInDTO:
    uuid: UUID
    name: str | None = None
    description: str | None = None
    status: str | None = None


@dataclass
class UpdateStageOutDTO:
    stage: entities.Stage


@dataclass
class DeleteStageInDTO:
    uuid: UUID


@dataclass
class GetStageListInDTO:
    project_uuid: UUID


@dataclass
class GetStageListOutDTO:
    stages: list[entities.Stage]
