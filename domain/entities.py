from dataclasses import dataclass
from uuid import UUID



@dataclass
class User:
    uuid: UUID
    name: str
    email: str
    password_hash: str
    creator_uuid: UUID
    is_active: bool
    is_archived: bool
    is_admin: bool

    def can_create_users(self) -> bool:
        return self.is_admin

    def can_update_users(self, user_projects_names: set[str], admin_projects_names: set[str]) -> bool:
        return user_projects_names <= admin_projects_names

    def can_get_users(self, projects_names: set[str] | None, user_projects_names: set[str]) -> bool:
        return self.is_admin and (user_projects_names <= projects_names if projects_names is not None else True)
    
@dataclass
class Project:
    uuid: UUID
    name: str
    description: str | None
    is_active: bool
    is_archived: bool
    is_blocked: bool
    created_at: str
    end_date: str | None
    creator: User
    completed: bool = False

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