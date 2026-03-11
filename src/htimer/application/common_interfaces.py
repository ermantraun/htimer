from abc import abstractmethod
from typing import Protocol, Any
from uuid import UUID
from dataclasses import dataclass
from datetime import date 
from htimer.domain import entities
from . import common_exceptions



@dataclass
class ActionLink:
    link: str | None = None


class DBSession(Protocol):
    @abstractmethod
    async def commit(self) -> None:
        pass

class TextNormalizer(Protocol):
    @abstractmethod
    def normalize(self, text: str) -> str:
        pass

class Context(Protocol):
    @abstractmethod
    def get_current_user_uuid(self) -> UUID | common_exceptions.InvalidTokenError:
        pass

class Logger(Protocol):
    @abstractmethod
    async def info(self, operation: str,  message: str) -> None:
        pass


class Clock(Protocol):
    @abstractmethod
    async def now_date(self) -> date:
        pass
    
    @abstractmethod
    def verify_date(self, date: str) -> str | common_exceptions.InvalidDate:
        pass
    
    @abstractmethod
    def verify_period(self, start_date: date | None, end_date: date | None) -> None | common_exceptions.InvalidDate:
        pass


class UserRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def update(self, user_uuid: UUID, data: dict[str, Any]) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    
class ProjectRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def update(self, project_uuid: UUID, data: dict[str, Any]) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_name(self, user_uuid: UUID, project_name: str) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def remove_members(self, project_uuid: UUID, members_uuids: list[
        UUID]) -> None | common_exceptions.MemberNotFound | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_members(self, projects_uuid: list[UUID], is_active: bool = True) -> list[entities.User] | common_exceptions.ProjectNotFoundError |common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_current_subscription(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:

        pass

    
class StageRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Stage) -> entities.Stage | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def update(self, stage_uuid: UUID, data: dict[str, Any]) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_children(self, stage_uuid: UUID) -> list[entities.Stage] | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def delete(self, stage_uuid: UUID) -> None | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass
    
class DailyLogRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.DailyLog) -> entities.DailyLog | common_exceptions.DailyLogAlreadyExistsError| common_exceptions.UserNotFoundError | common_exceptions.StageNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, day_uuid: UUID, lock_record: bool = False) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, day_uuid: UUID, data: dict[str, Any]) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list_by_project(self, project_uuid: UUID, start_date: date | None, end_date: date | None, users_uuid: list[UUID], draft: bool = False) -> list[entities.DailyLog] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    

    
class FileRepository(Protocol):
    @abstractmethod
    async def create(self, file: entities.DailyLogFile) -> entities.DailyLogFile | common_exceptions.FileAlreadyExistsError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get(self, file_uuid: UUID) -> entities.DailyLogFile | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def remove(self, file_uuid: UUID) -> entities.DailyLogFile | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, daily_log_uuid: UUID) -> list[entities.DailyLogFile] | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        pass


class TaskRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Task) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError | common_exceptions.StageNotFoundError | common_exceptions.UserNotFoundError:
        pass

    @abstractmethod
    async def get_by_uuid(self, task_uuid: UUID, lock_record: bool = False) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, task_uuid: UUID, data: dict[str, Any]) -> entities.Task | common_exceptions.TaskNotFoundError | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def delete(self, task_uuid: UUID) -> None | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, substage_uuid: UUID) -> list[entities.Task] | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list_by_project(self, project_uuid: UUID) -> list[entities.Task] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass

class PaymentRepository(Protocol):
    @abstractmethod
    async def create(self, payment: entities.Payment) -> entities.Payment | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, payment_uuid: UUID, lock_record: bool = False) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def update(self, payment_uuid: UUID, data: dict[str, Any]) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_gateway_payment_id(self, payment_uuid: UUID) -> str | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def payment_applied_to_subscription(self, payment_uuid: UUID) -> bool | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        pass


class SubscriptionRepository(Protocol):
    
    @abstractmethod
    async def create(self, subscription: entities.Subscription) -> entities.Subscription | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_by_project_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:

        pass

    @abstractmethod
    async def update(self, subscription_uuid: UUID, data: dict[str, Any]) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        pass

    
class PaymentGateway(Protocol):
    @abstractmethod
    async def create_payment(self, actor: entities.User, project: entities.Project, amount: float, payment: entities.Payment) -> tuple[str, UUID] | common_exceptions.PaymentFailedError:
        pass
    
    @abstractmethod
    async def verify_payment_complete(self, id_: str) -> bool | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError:
        pass
    
    @abstractmethod
    async def refund_payment(self, payment: entities.Payment, gateway_payment_id: str) -> bool | common_exceptions.PaymentRefundFailedError | common_exceptions.PaymentNotExistsError:
        pass

class ReportRepository(Protocol):
    @abstractmethod
    async def create(self, report: entities.Report) -> None | common_exceptions.RepositoryError | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError:
        pass
    
    @abstractmethod
    async def get_by_uuid(self, report_uuid: UUID) -> entities.Report | common_exceptions.ReportNotFoundError | common_exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def update(self, report_uuid: UUID, data: dict[str, Any]) -> entities.Report | common_exceptions.ReportNotFoundError | common_exceptions.RepositoryError:
        pass

class JobGateway(Protocol):
    @abstractmethod
    async def enqueue_report_generation(self, report: entities.Report) -> None | common_exceptions.RepositoryError | common_exceptions.JobGatewayError:
        pass

class FileStorage(Protocol):

    @abstractmethod
    async def save(self, file_name: str, content: bytes) -> None | common_exceptions.FileAlreadyExistsInStorageError | common_exceptions.FileStorageError:
        pass

    @abstractmethod
    async def get_unload_link(self, file_name: str) -> str | common_exceptions.FileNotFoundInStorageError | common_exceptions.FileStorageError:
        pass

    @abstractmethod
    async def get_upload_link(self, file_name: str) -> str | common_exceptions.FileAlreadyExistsInStorageError | common_exceptions.FileStorageError:
        pass

    @abstractmethod
    async def get_unload_link_list(self, files: list[str]) -> list[tuple[str, str]] | common_exceptions.FileNotFoundInStorageError | common_exceptions.FileStorageError:
        pass

    @abstractmethod
    async def remove(self, file_name: str) -> None | common_exceptions.FileNotFoundInStorageError | common_exceptions.FileStorageError:
        pass
