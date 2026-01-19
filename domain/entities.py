from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


# ===== Helpers for typed defaults =====

def _empty_str_list() -> list[str]:
    return []


def _empty_uuid_str_dict() -> dict[UUID, str]:
    return {}


def _empty_table_columns() -> list["TableColumn"]:
    return []


def _empty_table_rows() -> list["TableRow"]:
    return []


def _empty_str_object_dict() -> dict[str, object]:
    return {}


# ==================== ENUMS ====================

class UserRole(Enum):
    ADMIN = "admin"        # Администратор / Руководитель проекта
    EXECUTOR = "executor"  # Пользователь / Исполнитель


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
    TRIAL = "trial"
    ACTIVE = "active"
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


# ==================== AUTHORIZATION DECISIONS ====================


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
        FORBIDDEN_FOR_NON_PROJECT_ADMIN = "forbidden_for_non_project_admin"
    
    class GetProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class DecideGetProjectDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class CreateStageDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class UpdateStageDecision(Enum):
        ALLOWED = "allowed"
        FORBIDDEN_FOR_NON_MEMBER = "forbidden_for_non_member"
    
    class CreateDailyLogDecision(Enum):
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
    creator_uuid: UUID
    role: UserRole
    created_at: str
    status: UserStatus = UserStatus.ACTIVE
    last_login: str | None = None


    def decide_create_users(self) -> UserDecisions.CreateUserDecision:
        
        if self.role is UserRole.ADMIN:
            return UserDecisions.CreateUserDecision.ALLOWED
        else:
            return UserDecisions.CreateUserDecision.FORBIDDEN_FOR_NON_ADMIN

    
    def ensure_update(self, target: User, change_role: bool, change_status: bool) -> str:
        is_self_update = self.uuid == target.uuid

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
        """Решение о возможности обновления пользователя"""
 
        if self.uuid != target.creator_uuid:
            return UserDecisions.UpdateUserDecision.FORBIDDEN_FOR_NON_CREATOR
        else:
            return UserDecisions.UpdateUserDecision.ALLOWED

    def decid_create_daily_log(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.CreateDailyLogDecision:
        """Решение о возможности создания дневного лога"""
        
        if self.uuid not in {member.uuid for member in project_members} or self.uuid != project.creator.uuid:
            return UserDecisions.CreateDailyLogDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.CreateDailyLogDecision.ALLOWED

    def ensure_reset_password(self, target: User) -> str:
        return 'Нельзя сбросить пароль самому себе.' if self.uuid == target.uuid else ''

    
    def decide_reset_user_password(
        self,
        target: User,
    ) -> UserDecisions.ResetUserPasswordDecision:
        """Решение о возможности сброса пароля пользователя"""

        if self.uuid != target.creator_uuid:
            return UserDecisions.ResetUserPasswordDecision.FORBIDDEN_FOR_NON_CREATOR
        else:
            return UserDecisions.ResetUserPasswordDecision.ALLOWED
    
    def decide_create_project(self) -> UserDecisions.CreateProjectDecision:
        """Решение о возможности создания проекта"""
        if self.role is UserRole.ADMIN:
            return UserDecisions.CreateProjectDecision.ALLOWED
        else:
            return UserDecisions.CreateProjectDecision.FORBIDDEN_FOR_NON_ADMIN
    
    def decide_update_project(self, members: list[User]) -> UserDecisions.UpdateProjectDecision:
        """Решение о возможности обновления проекта"""
        if self.role is not UserRole.ADMIN or self.uuid not in {member.uuid for member in members}:
            return UserDecisions.UpdateProjectDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN

        return UserDecisions.UpdateProjectDecision.ALLOWED

    def decide_get_project(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.GetProjectDecision:
        """Решение о возможности получения проекта"""

        if self.uuid not in {member.uuid for member in project_members} or project.creator.uuid != self.uuid:
            return UserDecisions.GetProjectDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.GetProjectDecision.ALLOWED

    def decide_create_stage(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.CreateStageDecision:
        """Решение о возможности создания этапа"""

        if self.uuid not in {member.uuid for member in project_members}:
            return UserDecisions.CreateStageDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.CreateStageDecision.ALLOWED
    
    def decide_update_stage(
        self,
        project: Project,
        project_members: list[User],
    ) -> UserDecisions.UpdateStageDecision:
        """Решение о возможности обновления этапа"""
        
        if self.uuid not in {member.uuid for member in project_members} or project.creator.uuid != self.uuid:
            return UserDecisions.UpdateStageDecision.FORBIDDEN_FOR_NON_MEMBER

        return UserDecisions.UpdateStageDecision.ALLOWED
        
    

    
    def decide_get_users(
        self,
        *,
        requested_projects_names: set[str] | None,
        actor_projects_names: set[str],
    ) -> UserDecisions.ListUsersDecision:
        """Решение о возможности получения списка пользователей"""

        if requested_projects_names is not None and not requested_projects_names <= actor_projects_names:
            return UserDecisions.ListUsersDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN

        return UserDecisions.ListUsersDecision.ALLOWED


# ==================== PROJECT ====================

@dataclass
class Project:
    uuid: UUID
    name: str
    description: str | None
    creator: User
    created_at: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    start_date: str | None = None
    end_date: str | None = None
    

    def ensure_update(self) -> str:
        if self.status in {ProjectStatus.ARCHIVED, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED}:
            return "Нельзя изменить проект в архивном, заблокированном или завершённом статусе."
        return ""



# ==================== MEMBERSHIP ====================

@dataclass
class MemberShip:
    uuid: UUID
    user: User
    project: Project
    joined_at: str
    assigned_by: UUID | None = None

# ==================== STAGE ====================

@dataclass
class Stage:
    uuid: UUID
    name: str
    description: str | None
    creator: User
    created_at: str
    project: Project
    parent: Stage | None = None
    main_path: bool | None = None
    status: StageStatus = StageStatus.ACTIVE
    end_date: str | None = None

    def ensure_update(self) -> str:
        
        if self.status in {StageStatus.COMPLETED, StageStatus.ARCHIVED}:
            return "Нельзя изменить этап в завершённом или архивном статусе."

        return ''
    
    def complete(self) -> None:
        self.status = StageStatus.COMPLETED

    def archive(self) -> None:
        self.status = StageStatus.ARCHIVED


# ==================== TASK ====================

@dataclass
class Task:
    uuid: UUID
    name: str
    description: str
    creator: User
    created_at: str
    substage: Stage
    completed: bool = False
    status: TaskStatus = TaskStatus.PENDING
    completion_dates: list[str] = field(default_factory=_empty_str_list)

    
    
    def mark_completed(self, date: str) -> None:
        self.completed = True
        self.status = TaskStatus.COMPLETED
        if date not in self.completion_dates:
            self.completion_dates.append(date)

    def mark_in_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS

    def archive(self) -> None:
        self.status = TaskStatus.ARCHIVED


# ==================== DAY ENTRY ====================

@dataclass
class DailyLog:
    uuid: UUID
    creator: User
    project: Project
    created_at: str
    updated_at: str | None = None
    hours_spent: float = 0.0
    description: str = ""
    substage: Stage | None = None

    def update_description(self, description: str) -> None:
        self.description = description


    def set_substage(self, substage: Stage) -> None:
        self.substage = substage


    def update_hours(self, hours: float) -> None:
        self.hours_spent = hours



# ==================== DAY TASK LINK ====================

@dataclass
class DayTaskLink:
    uuid: UUID
    day_entry: DailyLog
    task: Task
    linked_at: str
    completed_today: bool = False
    notes: str | None = None

    def mark_completed(self, notes: str | None = None) -> None:
        self.completed_today = True
        if notes:
            self.notes = notes


# ==================== FILE ====================

@dataclass
class File:
    uuid: UUID
    filename: str
    url: str
    day_entry: DailyLog
    uploader: User
    uploaded_at: str
    file_size: int = 0  # bytes
    file_type: str | None = None

    def is_image(self) -> bool:
        image_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        return self.file_type in image_types if self.file_type else False


# ==================== TABLE ====================

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
    created_at: str
    updated_at: str
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


# ==================== DRAFT ====================

@dataclass
class Draft:
    uuid: UUID
    day_entry: DailyLog
    created_at: str
    updated_at: str 
    content: dict[str, object] = field(default_factory=_empty_str_object_dict)
    auto_saved: bool = True


    def update_content(self, content: dict[str, object]) -> None:
        self.content = content



# ==================== VOICE RECORD ====================

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


# ==================== SUBSCRIPTION ====================

@dataclass
class Subscribe:
    uuid: UUID
    project: Project
    plan_type: str
    start_date: str
    start_date: str
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    
    end_date: str | None = None
    auto_renew: bool = True

    def is_active(self, current_time: str) -> bool:
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.end_date:
            return datetime.fromisoformat(current_time) <= datetime.fromisoformat(self.end_date)
        return True

    def get_features_limit(self, current_time: str) -> dict[str, bool | int]:
        if self.status == SubscriptionStatus.ACTIVE and self.is_active(current_time):
            return {
                "can_export": True,
                "can_add_users": True,
                "can_add_projects": True,
                "max_users": 100,
                "max_projects": 50,
                "read_only": False,
            }
        elif self.status == SubscriptionStatus.TRIAL:
            return {
                "can_export": True,
                "can_add_users": True,
                "can_add_projects": True,
                "max_users": 5,
                "max_projects": 1,
                "read_only": False,
            }
        else:
            return {
                "can_export": False,
                "can_add_users": False,
                "can_add_projects": False,
                "read_only": True,
            }

    def expire(self) -> None:
        self.status = SubscriptionStatus.EXPIRED

    def cancel(self) -> None:
        self.status = SubscriptionStatus.CANCELLED
        self.auto_renew = False

    def renew(self, end_date: str) -> None:
        self.status = SubscriptionStatus.ACTIVE
        self.end_date = end_date


# ==================== PAYMENT ====================

@dataclass
class Payment:
    uuid: UUID
    subscription: Subscribe
    amount: float
    created_at: str
    currency: str = "RUB"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_date: str | None = None
    invoice_url: str | None = None
    receipt_url: str | None = None
    payment_method: str | None = None
    

    def complete(self, receipt_url: str | None = None) -> None:
        self.status = PaymentStatus.COMPLETED
        self.payment_date = datetime.now().isoformat()
        if receipt_url:
            self.receipt_url = receipt_url

    def fail(self) -> None:
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        self.status = PaymentStatus.REFUNDED


# ==================== REPORT ====================

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


# ==================== AUDIT LOG ====================

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