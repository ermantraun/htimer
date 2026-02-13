from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from uuid import UUID
from . import value_objects
    
"""
    todo: 
    1) Исправления - реализовать запрет создания подэтаппа в цепочке где есть незавершенные этапы
    2) реализовать корректное изменение статусов
    
    """

def _empty_uuid_str_dict() -> dict[UUID, str]:
    return {}


def _empty_table_columns() -> list["TableColumn"]:
    return []


def _empty_table_rows() -> list["TableRow"]:
    return []


def _empty_str_object_dict() -> dict[str, object]:
    return {}




class UserRole(Enum):
    ADMIN = "admin"        # Администратор / Руководитель проекта
    EXECUTOR = "executor"  # Пользователь / Исполнитель


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"

class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"
    COMPLETED = "completed"



class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"



class SubscriptionStatus(Enum):
    ACTIVE = "active"
    UNACTIVE = "unactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"



class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class TranscriptionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditAction(Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_ARCHIVED = "project_archived"
    REPORT_EXPORTED = "report_exported"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    DAY_ENTRY_CREATED = "day_entry_created"
    DAY_ENTRY_UPDATED = "day_entry_updated"




class StageStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"



class PaymentContext(Enum):
    OK = "ok"
    FAILED = "failed"
    


class UserDecisions:
    class CreateUserDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_ADMIN = "forbidden_for_non_admin"
    
    class UpdateUserDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_CREATOR = "forbidden_for_non_creator"


    class ListUsersDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_ADMIN = "forbidden_for_non_project_admin"

    class ResetUserPasswordDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_CREATOR = "forbidden_for_non_creator"

    class CreateProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_ADMIN = "forbidden_for_non_admin"
        
    class UpdateProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR = "FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR"
    
    class GetProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class DecideGetProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class DecideGetDailyLogListDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR = "forbidden_for_non_project_admin_or_creator"
    
    class CreateStageDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class UpdateStageDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class CreateDailyLogDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class UpdateDailyLogDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_CREATOR = "forbidden_for_non_creator"
        
    class GetDailyLogDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR = "forbidden_for_non_project_admin_or_creator"
    
    class CreateTaskDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"

    class CreateSubscriptionDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_CREATOR = "forbidden_for_non_project_creator"

    class CreatePaymentDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_PROJECT_CREATOR = "forbidden_for_non_project_creator"

    class UpdateTaskDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"

    class GetTaskDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"

    class DeleteTaskDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
# ==================== USER ====================

@dataclass
class User:
    """
    Пользователь системы.

    Роли:
    - role=ADMIN: Администратор/Руководитель проекта
    - role=EXECUTOR: Пользователь/Исполнитель
    """
    uuid: UUID
    name: str
    email: str
    password_hash: str
    creator: User
    role: UserRole
    created_at: date
    status: UserStatus = UserStatus.ACTIVE
    last_login: date | None = None


    def decide_create_users(self) -> UserDecisions.CreateUserDecision:
        
        if self.role is UserRole.ADMIN:
            return UserDecisions.CreateUserDecision.ALLOWED
        else:
            return UserDecisions.CreateUserDecision.FORBIDDEN_FOR_NON_ADMIN

    
    def ensure_update(self, target: User, change_role: bool, change_status: bool) -> str:
        is_self_update = self is target

        if is_self_update:
            if change_role:
                return 'Нельзя изменять роль самому себе.'

            if change_status:
                return 'Нельзя менять статус активности или архивности своего аккаунта.'

            return ''
        return ''
        
    def decide_update_user(
        self,
        target: User,
    ) -> UserDecisions.UpdateUserDecision:
 
        if self is not target.creator:
            return UserDecisions.UpdateUserDecision.FORBIDDEN_FOR_NON_CREATOR
        else:
            return UserDecisions.UpdateUserDecision.ALLOWED

    def decide_create_daily_log(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.CreateDailyLogDecision:
        
        if self.uuid not in {member.uuid for member in project_members} or self is not project.creator:
            return UserDecisions.CreateDailyLogDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.CreateDailyLogDecision.ALLOWED

    def decide_create_subscription(
        self,
        project: Project,
    ) -> UserDecisions.CreateSubscriptionDecision:

        if self is project.creator:
            return UserDecisions.CreateSubscriptionDecision.ALLOWED

        return UserDecisions.CreateSubscriptionDecision.FORBIDDEN_FOR_NON_PROJECT_CREATOR

    def decide_create_payment(
        self,
        project: Project,
    ) -> UserDecisions.CreatePaymentDecision:

        if self is project.creator:
            return UserDecisions.CreatePaymentDecision.ALLOWED

        return UserDecisions.CreatePaymentDecision.FORBIDDEN_FOR_NON_PROJECT_CREATOR

    def decide_update_daily_log(
        self,
        daily_log: DailyLog
    ) -> UserDecisions.UpdateDailyLogDecision:
        
        if daily_log.creator is not self:
            return UserDecisions.UpdateDailyLogDecision.FORBIDDEN_FOR_NON_CREATOR
        
        return UserDecisions.UpdateDailyLogDecision.ALLOWED

    def decide_get_daily_log(
        self,
        daily_log: DailyLog,
        project_members: list[User]
        
    ) -> UserDecisions.GetDailyLogDecision:
            
        if self is not daily_log.creator and self is not daily_log.project.creator and (self.role is not UserRole.ADMIN and self not in project_members):
                return UserDecisions.GetDailyLogDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR
        
        return UserDecisions.GetDailyLogDecision.ALLOWED
    
    def ensure_reset_password(self, target: User) -> str:
        return 'Нельзя сбросить пароль самому себе.' if self is target else ''

    
    def decide_reset_user_password(
        self,
        target: User,
    ) -> UserDecisions.ResetUserPasswordDecision:

        if self is not target and self is not target.creator:
            return UserDecisions.ResetUserPasswordDecision.FORBIDDEN_FOR_NON_CREATOR
        else:
            return UserDecisions.ResetUserPasswordDecision.ALLOWED
    
    def decide_create_project(self) -> UserDecisions.CreateProjectDecision:
        """Решение о возможности создания проекта"""
        if self.role is UserRole.ADMIN:
            return UserDecisions.CreateProjectDecision.ALLOWED
        else:
            return UserDecisions.CreateProjectDecision.FORBIDDEN_FOR_NON_ADMIN
    
    def decide_update_project(self, project: Project, members: list[User]) -> UserDecisions.UpdateProjectDecision:
        if self is not project.creator and (self.role is not UserRole.ADMIN and self not in members):
            return UserDecisions.UpdateProjectDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR

        return UserDecisions.UpdateProjectDecision.ALLOWED

    def decide_get_project(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.GetProjectDecision:

        if self.uuid not in {member.uuid for member in project_members} or project.creator.uuid != self.uuid:
            return UserDecisions.GetProjectDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.GetProjectDecision.ALLOWED

    def decide_get_daily_log_list(
        self, target: User, project: Project, project_members: list[User]
    ) -> UserDecisions.DecideGetDailyLogListDecision:
        
        if self is not target and self is not project.creator and (self.role is not UserRole.ADMIN and self not in project_members):
            return UserDecisions.DecideGetDailyLogListDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR

        return UserDecisions.DecideGetDailyLogListDecision.ALLOWED
        
    def decide_create_stage(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.CreateStageDecision:

        if self.uuid not in {member.uuid for member in project_members} or project.creator is not self:
            return UserDecisions.CreateStageDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.CreateStageDecision.ALLOWED

    def decide_create_task(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.CreateTaskDecision:

        if self.uuid not in {member.uuid for member in project_members} and self is not project.creator:
            return UserDecisions.CreateTaskDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.CreateTaskDecision.ALLOWED

    def decide_update_task(
        self,
        task: "Task",
        project_members: list[User],
    ) -> UserDecisions.UpdateTaskDecision:

        if self.uuid not in {member.uuid for member in project_members}:
            return UserDecisions.UpdateTaskDecision.FORBIDDEN_FOR_NON_MEMBER
        else:
            return UserDecisions.UpdateTaskDecision.ALLOWED

    def decide_get_task(
        self, task_project: Project,
        task_project_members: list[User],
    ) -> UserDecisions.GetTaskDecision:

        if self.uuid not in {member.uuid for member in task_project_members} and self is not task_project.creator:
            return UserDecisions.GetTaskDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.GetTaskDecision.ALLOWED

    def decide_delete_task(
        self,
        task: "Task",
        project_members: list[User],
    ) -> UserDecisions.DeleteTaskDecision:
        if self.uuid not in {member.uuid for member in project_members}:
            return UserDecisions.DeleteTaskDecision.FORBIDDEN_FOR_NON_MEMBER
        else:
            return UserDecisions.DeleteTaskDecision.ALLOWED
    
    def decide_update_stage(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.UpdateStageDecision:
        
        if self.uuid not in {member.uuid for member in project_members} or project.creator is not self:
            return UserDecisions.UpdateStageDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.UpdateStageDecision.ALLOWED
        
    
    def decide_get_users(
        self,
        *,
        requested_projects_names: set[str] | None,
        actor_projects_names: set[str],
    ) -> UserDecisions.ListUsersDecision:

        if requested_projects_names is not None and not ((requested_projects_names <= actor_projects_names) and self.creator.role is not UserRole.ADMIN):
            return UserDecisions.ListUsersDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN

        return UserDecisions.ListUsersDecision.ALLOWED


@dataclass
class Project:
    uuid: UUID
    name: str
    description: str | None
    creator: User
    created_at: date
    status: ProjectStatus = ProjectStatus.ACTIVE
    start_date: date | None = None
    end_date: date | None = None

    def ensure_update(self, subscription: 'Subscription | None' = None) -> str:
 
        if self.status in {ProjectStatus.ARCHIVED, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED}:
            return "Нельзя изменить проект в архивном, заблокированном или завершённом статусе."

        if self.status is not ProjectStatus.ACTIVE:
            if subscription is None:
                return "Нельзя изменить проект: проект не активен и нет активной подписки."
            if not subscription.is_active(datetime.now().isoformat()):
                return "Нельзя изменить проект: проект не активен и нет активной подписки."

        return ""

@dataclass
class Subscription:
    uuid: UUID
    project: Project
    created_at: date
    auto_renew: bool = True
    start_date: date | None = None
    end_date: date | None = None
    status: SubscriptionStatus = SubscriptionStatus.UNACTIVE


    def is_active(self, current_time: str) -> bool:
        if self.status == SubscriptionStatus.ACTIVE:
            return True

        if self.end_date is not None and datetime.fromisoformat(current_time) <= datetime.combine(self.end_date, datetime.min.time()):
            return True

        return False
    
    def expire(self) -> None:
        self.status = SubscriptionStatus.EXPIRED

    def cancel(self) -> None:
        self.status = SubscriptionStatus.CANCELLED
        self.auto_renew = False

    def ensure_create(self) -> str:

        if self.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя создать подписку для неактивного проекта."

        return ""

    def ensure_update(self, status: SubscriptionStatus | None) -> str:

        if self.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя изменить подписку для неактивного проекта."

        if self.status is SubscriptionStatus.CANCELLED:
            return "Нельзя изменить отменённую подписку."

        if status is not SubscriptionStatus.CANCELLED:
            return "Можно менять статус только на отмененную."

        return ""

    def ensure_extend(self) -> str:

        if self.status is SubscriptionStatus.CANCELLED:
            return "Нельзя продлить отменённую подписку."
        
        if not self.auto_renew:
            return "Нельзя продлить подписку с отключённым авто-продлением."

        if self.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя продлить подписку для неактивного проекта."

        return ""
    
    def ensure_activate(self) -> str:

        if self.status is not SubscriptionStatus.UNACTIVE:
            return "Можно активировать только неактивную подписку."

        if self.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя активировать подписку для неактивного проекта."

        return ""

@dataclass
class Payment:
    uuid: UUID
    subscription: Subscription
    amount: value_objects.MoneyAmount
    created_at: date
    status: PaymentStatus = PaymentStatus.PENDING
    payment_date: date | None = None
    payment_method: PaymentMethod | None = None
    

    def ensure_complete(self) -> str:
        
        if self.subscription.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя завершить платёж для подписки, если проект не активен."

        if self.subscription.status is SubscriptionStatus.CANCELLED:
            return "Нельзя завершить платёж для отменённой подписки."
        
        return ''

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        self.status = PaymentStatus.REFUNDED

    def ensure_create(self) -> str:

        if self.subscription.project.status is not ProjectStatus.ACTIVE:
            return "Нельзя создать платёж для подписки, если проект не активен."

        if self.subscription.status is SubscriptionStatus.CANCELLED:
            return "Нельзя завершить платёж для отменённой подписки."
        
        return ""

@dataclass
class MemberShip:
    uuid: UUID
    user: User
    project: Project
    joined_at: date
    assigned_by: User


@dataclass
class Stage:
    uuid: UUID
    name: str
    description: str | None
    creator: User
    created_at: date
    project: Project
    parent: Stage | None = None
    main_path: bool | None = None
    status: StageStatus = StageStatus.ACTIVE

    def ensure_update(self, subscription: Subscription | None = None) -> str:

        proj_err = self.project.ensure_update(subscription)
        if proj_err:
            return proj_err

        if self.status in {StageStatus.COMPLETED, StageStatus.ARCHIVED}:
            return "Нельзя изменить этап в завершённом или архивном статусе."

        return ''
    
    def complete(self) -> None:
        self.status = StageStatus.COMPLETED

    def archive(self) -> None:
        self.status = StageStatus.ARCHIVED
    
    def ensure_create(self, subscription: Subscription | None = None) -> str:
 
        proj_err = self.project.ensure_update(subscription)
        if proj_err:
            return proj_err

        return ""

@dataclass
class DailyLog:
    uuid: UUID
    creator: User
    project: Project
    created_at: date
    draft: bool = False
    updated_at: date | None = None
    hours_spent: float = 0.0
    description: str = ""
    substage: Stage | None = None

    def update_description(self, description: str) -> None:
        self.description = description

    def draft_viewers(self) -> list[User]:
        return [self.project.creator]

    def set_substage(self, substage: Stage) -> None:
        self.substage = substage


    def update_hours(self, hours: float) -> None:
        self.hours_spent = hours

@dataclass
class Task:
    uuid: UUID
    name: str
    description: str
    creator: User
    created_at: date
    substage: Stage
    status: TaskStatus = TaskStatus.PENDING
    working_dates: frozenset[date] = field(default_factory=frozenset) #type: ignore
    completion_date: date | None = None
    
    # def add_working_date(self, date: date) -> None:
    #     if date not in self.working_dates.dates:
    #         new_dates: tuple[date, ...] = self.working_dates.dates + (date,)
    #         self.working_dates = value_objects.WorkingDates(
    #             dates=new_dates,
    #         )
    
    # def mark_completed(self, date: date) -> None:
    #     self.status = TaskStatus.COMPLETED
    #     self.completion_dates.append(date)
    #     self.working_dates = value_objects.WorkingDates(
    #         dates=self.working_dates.dates,
    #     )

    # def mark_in_progress(self) -> None:
    #     self.status = TaskStatus.IN_PROGRESS

    # def archive(self) -> None:
    #     self.status = TaskStatus.ARCHIVED

    def ensure_update(self, subscription: 'Subscription | None' = None) -> str:
        """Проверяет возможность обновления задачи.

        Делегирует проверку проекту и затем выполняет проверки уровня задачи.
        """
    
        proj_err = self.substage.project.ensure_update(subscription)
        if proj_err:
            return proj_err

        if self.status is TaskStatus.COMPLETED:
            return "Нельзя изменить завершённую задачу."

        if self.substage.parent is None:
            return "Таск можно изменять только если он принадлежит подэтапу."
        return ""

    @staticmethod
    def ensure_create(substage: Stage, subscription: 'Subscription | None' = None) -> str:
        """Проверяет возможность создания задачи в подэтапе.

        Делегирует проверку проекту и затем проверяет, что создаём в подэтапе.
        """
    
        proj_err = substage.project.ensure_update(subscription)
        if proj_err:
            return proj_err

        if substage.parent is None:
            return "Таск можно создавать только в подэтапе."
        return ""


@dataclass
class File:
    uuid: UUID
    filename: str
    uri: str
    daily_log: DailyLog
    uploaded_at: date


@dataclass
class TableColumn:
    uuid: UUID
    name: str
    data_type: str
    order: int


@dataclass
class TableRow:
    uuid: UUID
    order: int
    cells: dict[UUID, str] = field(default_factory=_empty_uuid_str_dict)


@dataclass
class Table:
    uuid: UUID
    day_entry: DailyLog
    created_at: date
    updated_at: date
    columns: list[TableColumn] = field(default_factory=_empty_table_columns)
    rows: list[TableRow] = field(default_factory=_empty_table_rows)

    def add_column(self, name: str, data_type: str = "text") -> TableColumn:
        from uuid import uuid4
        new_column = TableColumn(
            uuid=uuid4(),
            name=name,
            data_type=data_type,
            order=len(self.columns),
        )
        self.columns.append(new_column)

        return new_column

    def add_row(self) -> TableRow:
        from uuid import uuid4
        new_row = TableRow(uuid=uuid4(), order=len(self.rows), cells={})
        self.rows.append(new_row)

        return new_row

    def update_cell(self, row_uuid: UUID, column_uuid: UUID, value: str) -> None:
        for row in self.rows:
            if row.uuid == row_uuid:
                row.cells[column_uuid] = value
        
                break


@dataclass
class VoiceRecord:
    uuid: UUID
    day_entry: DailyLog
    audio_file_url: str
    recorded_at: str
    transcription: str | None = None
    status: TranscriptionStatus = TranscriptionStatus.PENDING
    duration_seconds: float = 0.0
    

    def set_transcription(self, text: str) -> None:
        self.transcription = text
        self.status = TranscriptionStatus.COMPLETED

    def mark_failed(self) -> None:
        self.status = TranscriptionStatus.FAILED



@dataclass
class Report:
    uuid: UUID
    project: Project
    generated_by: User
    generated_at: str
    target_user: User | None = None
    start_date: str = ""
    end_date: str = ""
    file_path: str | None = None
    status: ReportStatus = ReportStatus.PENDING

    def is_user_report(self) -> bool:
        return self.target_user is not None

    def is_summary_report(self) -> bool:
        return self.target_user is None

    def mark_completed(self, file_path: str) -> None:
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path

    def mark_failed(self) -> None:
        self.status = ReportStatus.FAILED



@dataclass
class AuditLog:
    uuid: UUID
    user: User
    action: AuditAction
    timestamp: str
    entity_type: str
    entity_id: UUID | None = None
    details: dict[str, object] = field(default_factory=_empty_str_object_dict)
    ip_address: str | None = None

    def add_detail(self, key: str, value: object) -> None:
        self.details[key] = value