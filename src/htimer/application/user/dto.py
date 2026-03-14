from dataclasses import dataclass
from uuid import UUID

from htimer.domain import entities


@dataclass
class LoginUserInDTO:
    email: str
    password: str


@dataclass
class LoginUserOutDTO:
    token: str
    user_uuid: UUID


@dataclass
class CreateUserInDTO:
    name: str
    email: str
    password: str
    role: entities.UserRole


@dataclass
class CreateUserOutDTO:
    user_uuid: UUID


@dataclass
class ResetUserPasswordInDTO:
    user_uuid: UUID | None
    new_password: str


@dataclass
class UpdateUserInDTO:
    uuid: UUID | None
    name: str | None
    email: str | None
    password: str | None
    status: str | None
    role: str | None


@dataclass
class UpdateUserOutDTO:
    user: entities.User


@dataclass
class GetUserListInDTO:
    projects_names: set[str]
    is_active: bool | None


@dataclass
class GetUserListOutDTO:
    users: list[entities.User]
