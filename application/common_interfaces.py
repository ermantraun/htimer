from abc import abstractmethod
from typing import Protocol, Any
from uuid import UUID
from domain import entities
import common_exceptions


class DBSession(Protocol):
    @abstractmethod
    async def commit(self) -> None:
        pass



class TextNormalizer(Protocol):
    @abstractmethod
    def normalize(self, text: str) -> str:
        pass

class UserContext(Protocol):
    @abstractmethod
    def get_current_user_uuid(self) -> UUID | common_exceptions.InvalidToken:
        pass

class Logger(Protocol):
    @abstractmethod
    def info(self, operation: str,  message: str) -> None:
        pass


class Clock(Protocol):
    @abstractmethod
    def now_date(self) -> str:
        pass
    
    @abstractmethod
    def verify_date(self) -> str | common_exceptions.InvalidDate:
        pass

class UserRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError:
        pass
    
    @abstractmethod
    async def update(self, user_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.User | common_exceptions.EmailAlreadyExistsError:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError:
        pass
    
    @abstractmethod
    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError:
        pass
    
    @abstractmethod
    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError:
        pass
    
    
class ProjectRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError:
        pass
    
    @abstractmethod
    async def update(self, data: dict[str, Any], release_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_name(self, user_uuid: UUID, project_name: str, ) -> entities.Project | common_exceptions.ProjectNotFoundError:
        pass
    
    @abstractmethod
    async def add_members(self, project_uuid: UUID, members_uuids: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError:
        pass
    
    @abstractmethod
    async def remove_members(self, project_uuid: UUID, members_uuids: list[
        UUID]) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserNotProjectMemberError:
        pass
    
    @abstractmethod
    async def get_members(self, projects_uuid: list[UUID], is_active: bool = True) -> list[entities.User] | common_exceptions.ProjectNotFoundError:
        pass
    
class StageRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Stage) -> entities.Stage | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError:
        pass
    
    @abstractmethod
    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | common_exceptions.ProjectNotFoundError:
        pass
    
    @abstractmethod
    async def update(self, stage_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError:
        pass
    
class DailyLogRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.DailyLog) -> entities.DailyLog | common_exceptions.DailyLogAlreadyExistsError| common_exceptions.UserNotFoundError | common_exceptions.StageNotFoundError | common_exceptions.ProjectNotFoundError:
        pass

    
    