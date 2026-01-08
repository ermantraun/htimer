"""
Domain entities.

User and Project have been moved to modules/users/domain/entities.py as part of
the Users bounded context refactoring. This file provides backward compatibility imports.

TODO: Refactor remaining entities into appropriate bounded contexts.
"""
from dataclasses import dataclass
from uuid import UUID

# Import User and Project from the new location for backward compatibility
from modules.users.domain.entities import User, Project


@dataclass
class MemberShip:
    uuid: UUID
    user: User
    project: Project
    joined_at: str
    is_active: bool

@dataclass   
class Stage:
    uuid: UUID
    name: str
    description: str
    created_at: str
    end_date: str | None
    creator: User
    project: Project
    completed: bool = False

@dataclass    
class SubStage:
    uuid: UUID
    name: str
    description: str
    created_at: str
    end_date: str
    creator: User
    stage: Stage

@dataclass
class Task:
    uuid: UUID
    name: str
    description: str
    completion_dates: list[str]
    completed: bool
    substage: SubStage
    creator: User


@dataclass
class DayEntry:
    uuid: UUID
    date: str
    hours_spent: float
    description: str
    creator: User
    task: Task | None
    substage: SubStage | None

@dataclass    
class File:
    uuid: UUID
    filename: str
    url: str
    uploaded_at: str
    uploader: User
    day_entry: DayEntry


@dataclass
class Subscribe:
    uuid: UUID
    user: User
    project: Project
    

@dataclass    
class Table:
    uuid: UUID
    day_entry: DayEntry
    
@dataclass
class Draft:
    uuid: UUID
    content: str
    day_entry: DayEntry