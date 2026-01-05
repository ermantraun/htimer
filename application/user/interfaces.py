from abc import abstractmethod
from typing import Protocol
from uuid import UUID
from domain import entities
from ..common_interfaces import DBSession
from .dto import UpdateUserInDTO
from . import exceptions


class UserCreator(Protocol):
    
    @abstractmethod
    def __init__(self, session: DBSession) -> None:
        pass
    
    @abstractmethod
    async def create(self, data: entities.User) -> entities.User | exceptions.EmailAlreadyExistsError:
        pass
    
class UserUpdater(Protocol):
    
    @abstractmethod
    def __init__(self, session: DBSession) -> None:
        pass
    
    @abstractmethod
    async def update(self, data: UpdateUserInDTO) -> entities.User | exceptions.EmailAlreadyExistsError:
        pass

class UserGetter(Protocol):
    
    @abstractmethod
    def __init__(self, session: DBSession) -> None:
        pass
    
    @abstractmethod
    async def get(self, user_uuid: UUID) -> entities.User | exceptions.UserNotFoundError:
        pass

class UserContext(Protocol):
    @abstractmethod
    def get_current_user_uuid(self) -> UUID | exceptions.InvalidToken:
        pass
    
    
class HashGenerator(Protocol):
    @abstractmethod
    def generate(self, plain_password: str) -> str:
        pass
    
class UserProjectsGetter(Protocol):
    
    @abstractmethod
    def __init__(self, session: DBSession) -> None:
        pass
    
    @abstractmethod
    async def get(self, user_uuid: UUID) -> set[entities.Project] | exceptions.UserNotFoundError:
        pass


class ProjectsUsersGetter(Protocol):
    
    @abstractmethod
    def __init__(self, session: DBSession) -> None:
        pass
    
    @abstractmethod
    async def get(self, projects_uuid: list[UUID] | None, is_active: bool | None) -> list[entities.User] | exceptions.UserNotFoundError:
        pass

