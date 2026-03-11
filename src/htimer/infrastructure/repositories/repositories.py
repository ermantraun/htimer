from datetime import date
from typing import Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities
from . import exceptions as db_exceptions, interfaces


_EXCEPTION_MAP: dict[type[BaseException], type[BaseException]] = {
    db_exceptions.EmailAlreadyExistsError: common_exceptions.EmailAlreadyExistsError,
    db_exceptions.UserNotFoundError: common_exceptions.UserNotFoundError,
    db_exceptions.UserRepositoryError: common_exceptions.UserRepositoryError,
    db_exceptions.UserAlreadyHasProjectError: common_exceptions.UserAlreadyHasProjectError,
    db_exceptions.ProjectNotFoundError: common_exceptions.ProjectNotFoundError,
    db_exceptions.ProjectRepositoryError: common_exceptions.ProjectRepositoryError,
    db_exceptions.MemberNotFound: common_exceptions.MemberNotFound,
    db_exceptions.UserAlreadyProjectMemberError: common_exceptions.UserAlreadyProjectMemberError,
    db_exceptions.StageAlreadyExistsError: common_exceptions.StageAlreadyExistsError,
    db_exceptions.ParentStageAlreadyHasMainSubStageError: common_exceptions.ParentStageAlreadyHasMainSubStageError,
    db_exceptions.StageNotFoundError: common_exceptions.StageNotFoundError,
    db_exceptions.StageRepositoryError: common_exceptions.StageRepositoryError,
    db_exceptions.DailyLogAlreadyExistsError: common_exceptions.DailyLogAlreadyExistsError,
    db_exceptions.DailyLogNotFoundError: common_exceptions.DailyLogNotFoundError,
    db_exceptions.DailyLogRepositoryError: common_exceptions.DailyLogRepositoryError,
    db_exceptions.TaskAlreadyExistsError: common_exceptions.TaskAlreadyExistsError,
    db_exceptions.TaskNotFoundError: common_exceptions.TaskNotFoundError,
    db_exceptions.TaskRepositoryError: common_exceptions.TaskRepositoryError,
    db_exceptions.PaymentNotFoundError: common_exceptions.PaymentNotFoundError,
    db_exceptions.PaymentRepositoryError: common_exceptions.PaymentRepositoryError,
    db_exceptions.SubscriptionAlreadyExistsError: common_exceptions.SubscriptionAlreadyExistsError,
    db_exceptions.SubscriptionNotFoundError: common_exceptions.SubscriptionNotFoundError,
    db_exceptions.SubscriptionRepositoryError: common_exceptions.SubscriptionRepositoryError,
    db_exceptions.FileAlreadyExistsError: common_exceptions.FileAlreadyExistsError,
    db_exceptions.FileNotFoundError: common_exceptions.FileNotFoundError,
    db_exceptions.FileRepositoryError: common_exceptions.FileRepositoryError,
    db_exceptions.ReportNotFoundError: common_exceptions.ReportNotFoundError,
    db_exceptions.ReportRepositoryError: common_exceptions.ReportRepositoryError,
    db_exceptions.RepositoryError: common_exceptions.RepositoryError,

}


def _map_exception(value: Any) -> Any:
    if not isinstance(value, BaseException):
        return value

    target_cls = _EXCEPTION_MAP.get(type(value))
    if target_cls is None:
        return value

    return target_cls(str(value))


class UserRepository(common_interfaces.UserRepository):
    def __init__(self, primary: interfaces.DBUserRepository):
        self._db_rep = primary

    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(data))

    async def update(self, user_uuid: UUID, data: dict[str, Any]) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(user_uuid, data))

    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_email(email))

    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(user_uuid, lock_record))

    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_list(users_uuid))

    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_projects(user_uuid))


class ProjectRepository(common_interfaces.ProjectRepository):
    def __init__(self, primary: interfaces.DBProjectRepository):
        self._db_rep = primary

    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(data))

    async def update(self, project_uuid: UUID, data: dict[str, Any]) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(project_uuid, data))

    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(project_uuid, lock_record))

    async def get_by_name(self, user_uuid: UUID, project_name: str) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_name(user_uuid, project_name))

    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.add_members(members))

    async def remove_members(self, project_uuid: UUID, members_uuids: list[UUID]) -> None | common_exceptions.MemberNotFound | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.remove_members(project_uuid, members_uuids))

    async def get_members(self, projects_uuid: list[UUID], is_active: bool = True) -> list[entities.User] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_members(projects_uuid, is_active))

    async def get_current_subscription(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_current_subscription(project_uuid))


class StageRepository(common_interfaces.StageRepository):
    def __init__(self, primary: interfaces.DBStageRepository):
        self._db_rep = primary

    async def create(self, data: entities.Stage) -> entities.Stage | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(data))

    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_list(project_uuid))

    async def update(self, stage_uuid: UUID, data: dict[str, Any]) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(stage_uuid, data))

    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(stage_uuid, lock_record))

    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_name(project_uuid, stage_name, lock_record))

    async def get_children(self, stage_uuid: UUID) -> list[entities.Stage] | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_children(stage_uuid))

    async def delete(self, stage_uuid: UUID) -> None | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.delete(stage_uuid))


class DailyLogRepository(common_interfaces.DailyLogRepository):
    def __init__(self, primary: interfaces.DBDailyLogRepository):
        self._db_rep = primary

    async def create(self, data: entities.DailyLog) -> entities.DailyLog | common_exceptions.DailyLogAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.StageNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(data))

    async def get_by_uuid(self, day_uuid: UUID, lock_record: bool = False) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(day_uuid, lock_record))

    async def update(self, day_uuid: UUID, data: dict[str, Any]) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(day_uuid, data))

    async def get_list_by_project(self, project_uuid: UUID, start_date: date | None, end_date: date | None, users_uuid: list[UUID], draft: bool = False) ->  list[entities.DailyLog] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_list_by_project(project_uuid, start_date, end_date, users_uuid, draft))


class TaskRepository(common_interfaces.TaskRepository):
    def __init__(self, primary: interfaces.DBTaskRepository):
        self._db_rep = primary

    async def create(self, data: entities.Task) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError | common_exceptions.StageNotFoundError | common_exceptions.UserNotFoundError:
        return _map_exception(await self._db_rep.create(data))

    async def get_by_uuid(self, task_uuid: UUID, lock_record: bool = False) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(task_uuid, lock_record))

    async def update(self, task_uuid: UUID, data: dict[str, Any]) -> entities.Task | common_exceptions.TaskNotFoundError | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(task_uuid, data))

    async def delete(self, task_uuid: UUID) -> None | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.delete(task_uuid))

    async def get_list(self, substage_uuid: UUID) -> list[entities.Task] | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_list(substage_uuid))

    async def get_list_by_project(self, project_uuid: UUID) -> list[entities.Task] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_list_by_project(project_uuid))

class PaymentRepository(common_interfaces.PaymentRepository):
    def __init__(self, primary: interfaces.DBPaymentRepository):
        self._db_rep = primary

    async def create(self, payment: entities.Payment) -> entities.Payment | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(payment))

    async def get_by_uuid(self, payment_uuid: UUID, lock_record: bool = False) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(payment_uuid, lock_record))

    async def update(self, payment_uuid: UUID, data: dict[str, Any]) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(payment_uuid, data))

    async def get_gateway_payment_id(self, payment_uuid: UUID) -> str | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_gateway_payment_id(payment_uuid))
    
    async def payment_applied_to_subscription(self, payment_uuid: UUID) -> bool | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.payment_applied_to_subscription(payment_uuid))

class SubscriptionRepository(common_interfaces.SubscriptionRepository):
    def __init__(self, primary: interfaces.DBSubscriptionRepository):
        self._db_rep = primary

    async def create(self, subscription: entities.Subscription) -> entities.Subscription | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.create(subscription))

    async def get_by_project_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_project_uuid(project_uuid, lock_record))

    async def update(self, subscription_uuid: UUID, data: dict[str, Any]) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(subscription_uuid, data))

class FileRepository(common_interfaces.FileRepository):
    def __init__(self, session: AsyncSession, db_rep: interfaces.DBFileRepository):
        self._session = session
        self._db_rep = db_rep

    async def create(self, file: entities.DailyLogFile) -> entities.DailyLogFile | common_exceptions.FileAlreadyExistsError | common_exceptions.RepositoryError:
        db_result = await self._db_rep.create(file)
        if isinstance(db_result, BaseException):
            return _map_exception(db_result)

        return db_result

    async def get(self, file_uuid: UUID) -> entities.DailyLogFile | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        db_result = await self._db_rep.get(file_uuid)
        if isinstance(db_result, BaseException):
            return _map_exception(db_result)

        return db_result

    async def remove(self, file_uuid: UUID) -> entities.DailyLogFile | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        db_result = await self._db_rep.remove(file_uuid)
        if isinstance(db_result, BaseException):
            return _map_exception(db_result)

        return db_result

    async def get_list(self, daily_log_uuid: UUID) -> list[entities.DailyLogFile] | common_exceptions.FileNotFoundError | common_exceptions.RepositoryError:
        db_result = await self._db_rep.get_list(daily_log_uuid)
        if isinstance(db_result, BaseException):
            return _map_exception(db_result)

        return db_result

class ReportRepository(common_interfaces.ReportRepository):
    def __init__(self, primary: interfaces.DBReportRepository):
        self._db_rep = primary

    async def create(self, report: entities.Report) -> None | common_exceptions.RepositoryError | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError:
        return _map_exception(await self._db_rep.create(report))

    async def get_by_uuid(self, report_uuid: UUID, lock_record: bool = False) -> entities.Report | common_exceptions.ReportNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.get_by_uuid(report_uuid, lock_record))
    
    async def update(self, report_uuid: UUID, data: dict[str, Any]) -> entities.Report | common_exceptions.ReportNotFoundError | common_exceptions.RepositoryError:
        return _map_exception(await self._db_rep.update(report_uuid, data))