from dataclasses import dataclass
from uuid import UUID

@dataclass
class CreateUserInDTO:
    name: str
    email: str
    password: str
    is_admin: bool
    is_archived: bool | None = False
    is_active: bool | None = True

@dataclass
class CreateUserOutDTO:
    name: str
    email: str
    is_active: bool
    is_archived: bool
    is_admin: bool

@dataclass
class UpdateUserInDTO:
    uuid: UUID | None
    name: str | None
    email: str | None
    password: str | None
    is_active: bool | None 
    is_archived: bool | None
    is_admin: bool | None
    
@dataclass
class UpdateUserOutDTO:
    name: str
    email: str
    is_active: bool
    is_archived: bool
    is_admin: bool
    
    
@dataclass
class GetUsersInDto:
    projects_names: set[str] | None
    status: bool | None  # 'active' or 'all'
    
@dataclass
class GetUserIn:
    name: str
    email: str
    is_active: bool
    is_archived: bool
    is_admin: bool
    
        
    
@dataclass
class GetUsersOutDTO:
    users: list[GetUserIn]