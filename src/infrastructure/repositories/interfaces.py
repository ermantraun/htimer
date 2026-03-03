from abc import abstractmethod
from datetime import date
from typing import Any, Protocol
from uuid import UUID
from domain import entities

from . import exceptions

class DBUserRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.User) -> entities.User | exceptions.EmailAlreadyExistsError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, user_uuid: UUID, data: dict[str, Any]) -> entities.User | exceptions.EmailAlreadyExistsError | exceptions.UserNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> entities.User | exceptions.UserNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | exceptions.UserNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | exceptions.UserNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | exceptions.UserNotFoundError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass


class DBProjectRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Project) -> entities.Project | exceptions.UserAlreadyHasProjectError | exceptions.UserNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, project_uuid: UUID, data: dict[str, Any]) -> entities.Project | exceptions.ProjectNotFoundError | exceptions.UserAlreadyHasProjectError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_name(self, user_uuid: UUID, project_name: str) -> entities.Project | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | exceptions.ProjectNotFoundError | exceptions.UserNotFoundError | exceptions.UserAlreadyProjectMemberError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def remove_members(self, project_uuid: UUID, members_uuids: list[UUID]) -> None | exceptions.MemberNotFound | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_members(self, projects_uuid: list[UUID], is_active: bool = True) -> list[entities.User] | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_current_subscription(self, project_uuid: UUID) -> entities.Subscription | exceptions.SubscriptionNotFoundError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass


class DBStageRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Stage) -> entities.Stage | exceptions.StageAlreadyExistsError | exceptions.ParentStageAlreadyHasMainSubStageError | exceptions.UserNotFoundError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, stage_uuid: UUID, data: dict[str, Any]) -> entities.Stage | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_children(self, stage_uuid: UUID) -> list[entities.Stage] | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def delete(self, stage_uuid: UUID) -> None | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass


class DBDailyLogRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.DailyLog) -> entities.DailyLog | exceptions.DailyLogAlreadyExistsError | exceptions.UserNotFoundError | exceptions.StageNotFoundError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_uuid(self, day_uuid: UUID, lock_record: bool = False) -> entities.DailyLog | exceptions.DailyLogNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, day_uuid: UUID, data: dict[str, Any]) -> entities.DailyLog | exceptions.DailyLogNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list_by_project(self, project_uuid: UUID, start_date: date | None, end_date: date | None, users_uuid: list[UUID], draft: bool = False) -> list[entities.DailyLog] | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass


class DBTaskRepository(Protocol):
    @abstractmethod
    async def create(self, data: entities.Task) -> entities.Task | exceptions.TaskAlreadyExistsError | exceptions.RepositoryError | exceptions.StageNotFoundError | exceptions.UserNotFoundError:
        pass

    @abstractmethod
    async def get_by_uuid(self, task_uuid: UUID, lock_record: bool = False) -> entities.Task | exceptions.TaskAlreadyExistsError | exceptions.TaskNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, task_uuid: UUID, data: dict[str, Any]) -> entities.Task | exceptions.TaskNotFoundError | exceptions.TaskAlreadyExistsError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def delete(self, task_uuid: UUID) -> None | exceptions.TaskNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, substage_uuid: UUID) -> list[entities.Task] | exceptions.StageNotFoundError | exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_list_by_project(self, project_uuid: UUID) -> list[entities.Task] | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

class DBPaymentRepository(Protocol):
    @abstractmethod
    async def create(self, payment: entities.Payment) -> entities.Payment | exceptions.SubscriptionNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_uuid(self, payment_uuid: UUID, lock_record: bool = False) -> entities.Payment | exceptions.PaymentNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, payment_uuid: UUID, data: dict[str, Any]) -> entities.Payment | exceptions.PaymentNotFoundError | exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def get_gateway_payment_id(self, payment_uuid: UUID) -> str | exceptions.PaymentNotFoundError | exceptions.RepositoryError:
        pass
    
    @abstractmethod
    async def payment_applied_to_subscription(self, payment_uuid: UUID) -> bool | exceptions.PaymentNotFoundError | exceptions.RepositoryError:
        pass


class DBSubscriptionRepository(Protocol):
    @abstractmethod
    async def create(self, subscription: entities.Subscription) -> entities.Subscription | exceptions.SubscriptionAlreadyExistsError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_by_project_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Subscription | exceptions.SubscriptionNotFoundError | exceptions.ProjectNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def update(self, subscription_uuid: UUID, data: dict[str, Any]) -> entities.Subscription | exceptions.SubscriptionNotFoundError | exceptions.RepositoryError:
        pass

class DBFileRepository(Protocol):
    @abstractmethod
    async def create(self, file: entities.DailyLogFile) -> entities.DailyLogFile | exceptions.FileAlreadyExistsError | exceptions.RepositoryError:

        pass

    @abstractmethod
    async def get(self, file_uuid: UUID) -> entities.DailyLogFile | exceptions.FileNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def remove(self, file_uuid: UUID) -> entities.DailyLogFile | exceptions.FileNotFoundError | exceptions.RepositoryError:
        pass

    @abstractmethod
    async def get_list(self, daily_log_uuid: UUID) -> list[entities.DailyLogFile] | exceptions.FileNotFoundError | exceptions.RepositoryError:
        pass

class DBReportRepository(Protocol):
    @abstractmethod
    async def create(self, report: entities.Report) -> entities.Report | exceptions.RepositoryError | exceptions.ProjectNotFoundError | exceptions.UserNotFoundError:
        pass

    @abstractmethod
    async def get_by_uuid(self, report_uuid: UUID, lock_record: bool = False) -> entities.Report | exceptions.ReportNotFoundError | exceptions.RepositoryError:
        pass
class StorageFileRepository(Protocol):
    @abstractmethod
    async def get_upload_link(self, file: entities.DailyLogFile) -> str | exceptions.FileRepositoryError:
        pass

    @abstractmethod
    async def get_unload_link(self, file: entities.DailyLogFile) -> str | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        pass
    
    @abstractmethod
    async def get_unload_link_list(self, files: list[entities.DailyLogFile]) -> list[tuple[entities.DailyLogFile, str]] | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        pass

    @abstractmethod
    async def get_remove_link(self, file: entities.DailyLogFile) -> None | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        pass


