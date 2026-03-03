from dataclasses import dataclass
from uuid import UUID
from domain import entities

@dataclass
class CreateTaskInDTO:
    name: str
    description: str
    substage_uuid: UUID

@dataclass
class CreateTaskOutDTO:
    task: entities.Task


@dataclass
class GetTaskInDTO:
    uuid: UUID

@dataclass
class GetTaskOutDTO:
    task: entities.Task


@dataclass
class UpdateTaskInDTO:
    uuid: UUID
    name: str | None = None
    description: str | None = None
    substage_uuid: UUID | None = None
    completed: bool | None = None

@dataclass
class UpdateTaskOutDTO:
    task: entities.Task


@dataclass
class DeleteTaskInDTO:
    uuid: UUID


@dataclass
class ListTasksInDTO:
    substage_uuid: UUID


@dataclass
class ListTasksOutDTO:
    tasks: list[entities.Task]
