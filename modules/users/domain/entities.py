"""Domain entities for the Users bounded context."""
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
    """
    Project entity - included in Users context because it's referenced by user operations.
    This is a read-only reference from the Users context perspective.
    """
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
