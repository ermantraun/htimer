from abc import abstractmethod
from typing import Protocol, Any
from uuid import UUID
from datetime import date 
from domain import entities
from . import common_exceptions


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
    def now_date(self) -> date:
        pass
    
    @abstractmethod
    def verify_date(self) -> str | common_exceptions.InvalidDate:
        pass


class UserRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserRepositoryError:
        pass
    
    @abstractmethod
    async def update(self, user_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        pass
    
    @abstractmethod
    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        pass
    
    @abstractmethod
    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        pass
    
    
class ProjectRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError | common_exceptions.ProjectRepositoryError:
        pass
    
    @abstractmethod
    async def update(self, project_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.ProjectRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.ProjectRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_name(self, user_uuid: UUID, project_name: str, ) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.ProjectRepositoryError:
        pass
    
    @abstractmethod
    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | common_exceptions.ProjectRepositoryError:
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
    async def create(self, data: entities.Stage) -> entities.Stage | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
    @abstractmethod
    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | common_exceptions.ProjectNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
    @abstractmethod
    async def update(self, stage_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
    @abstractmethod
    async def delete(self, stage_uuid: UUID, release_record: bool = False) -> None | common_exceptions.StageNotFoundError | common_exceptions.StageRepositoryError:
        pass
    
class DailyLogRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.DailyLog) -> entities.DailyLog | common_exceptions.DailyLogAlreadyExistsError| common_exceptions.UserNotFoundError | common_exceptions.StageNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.DailyLogRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, day_uuid: UUID, lock_record: bool = False) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.DailyLogRepositoryError:
        pass

    @abstractmethod
    async def update(self, day_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.DailyLogRepositoryError:
        pass

    @abstractmethod
    async def get_list(self, project_uuid: UUID, date: str, draft: bool = False) -> list[entities.DailyLog] | common_exceptions.ProjectNotFoundError | common_exceptions.DailyLogRepositoryError:
        pass
    
    
    
class FileRepository(Protocol):
    @abstractmethod
    async def create(self, file: entities.File) -> entities.File:
        """Create (store) file metadata (and/or content) for a daily log and return the stored File entity.

        Note: takes daily_log UUID and file name per interface contract.
        """
        pass

    @abstractmethod
    async def get(self, daily_log_uuid: UUID, file_uuid: UUID) -> entities.File:
        """Return file metadata for a given daily_log UUID and file UUID."""
        pass

    @abstractmethod
    async def remove(self, daily_log_uuid: UUID, file_uuid: UUID) -> entities.File:
        """Remove file and return removed File entity (or record of removal)."""
        pass

    @abstractmethod
    async def get_list(self, daily_log_uuid: UUID) -> list[entities.File]:
        """Return list of File entities attached to the given daily_log UUID."""
        pass


class TaskRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Task) -> entities.Task | common_exceptions.TaskRepositoryError:
        """Create a Task entity and return stored Task."""
        pass

    @abstractmethod
    async def get_by_uuid(self, task_uuid: UUID, lock_record: bool = False) -> entities.Task | common_exceptions.TaskNotFoundError | common_exceptions.TaskRepositoryError:
        pass

    @abstractmethod
    async def update(self, task_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Task | common_exceptions.TaskNotFoundError | common_exceptions.TaskRepositoryError:
        pass

    @abstractmethod
    async def delete(self, task_uuid: UUID, release_record: bool = False) -> None | common_exceptions.TaskNotFoundError | common_exceptions.TaskRepositoryError:
        pass

    @abstractmethod
    async def get_list(self, substage_uuid: UUID) -> list[entities.Task] | common_exceptions.StageNotFoundError | common_exceptions.TaskRepositoryError:
        pass

class PaymentRepository(Protocol):
    @abstractmethod
    async def create(self, payment: entities.Payment) -> entities.Payment | common_exceptions.SubscriptionNotFoundError | common_exceptions.PaymentRepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, payment_uuid: UUID, lock_record: bool = False) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentRepositoryError:
        pass
    
    @abstractmethod
    async def update(self, payment_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentRepositoryError:
        pass

class SubscriptionRepository(Protocol):
    
    @abstractmethod
    async def create(self, subscription: entities.Subscription) -> entities.Subscription | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.SubscriptionRepositoryError:
        pass

    @abstractmethod
    async def has_active_subscription(self, project_uuid: UUID) -> bool | common_exceptions.ProjectNotFoundError | common_exceptions.SubscriptionRepositoryError:

        pass
    
    @abstractmethod
    async def get_by_project_uuid(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.SubscriptionRepositoryError:

        pass

    @abstractmethod
    async def update(self, subscription_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.SubscriptionRepositoryError:
        pass

    @abstractmethod
    async def get_active_subscription(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.SubscriptionRepositoryError:

        pass
    
    
class PaymentGateway(Protocol):
    @abstractmethod
    async def get_process_payment_link(self, amount: float, payment: entities.Payment) -> str | common_exceptions.PaymentFailedError:
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_uuid: UUID) -> bool | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError:
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_uuid: UUID) -> bool | common_exceptions.PaymentRefundFailedError | common_exceptions.PaymentNotExistsError:
        pass