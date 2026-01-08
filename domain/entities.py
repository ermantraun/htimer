from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID
from datetime import datetime


# ==================== ENUMS ====================

class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"


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

class UpdateUserDecision(Enum):
    ALLOWED = "allowed"
    SELF_ADMIN_CHANGE_FORBIDDEN = "self_admin_change_forbidden"
    SELF_STATUS_CHANGE_FORBIDDEN = "self_status_change_forbidden"
    PROJECT_CONTEXT_MISSING = "project_context_missing"
    TARGET_PROJECT_NOT_OWNED = "target_project_not_owned"


class ListUsersDecision(Enum):
    ALLOWED = "allowed"
    NOT_ADMIN = "not_admin"
    PROJECT_ACCESS_DENIED = "project_access_denied"


# ==================== USER ====================

@dataclass
class User:
    """
    Пользователь системы. 
    
    Роли:
    - is_admin=True: Администратор/Руководитель проекта
    - is_admin=False: Пользователь/Исполнитель
    
    Администратор может:
    - Создавать и управлять пользователями
    - Создавать и управлять проектами
    - Просматривать работу всех пользователей
    - Экспортировать отчеты
    - Управлять оплатой
    
    Пользователь может:
    - Вести календарный план (этапы/подэтапы)
    - Создавать ежедневные записи
    - Управлять задачами
    - Экспортировать свои отчеты
    """
    uuid: UUID
    name: str
    email: str
    password_hash: str
    creator_uuid: UUID
    is_active: bool
    is_archived: bool
    is_admin: bool
    status: UserStatus = UserStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: str | None = None

    def can_create_users(self) -> bool:
        """Только администраторы могут создавать пользователей"""
        return self.is_admin

    def can_update_users(self, user_projects_names: set[str], admin_projects_names: set[str]) -> bool:
        """Администратор может обновлять пользователей только в своих проектах"""
        return user_projects_names <= admin_projects_names

    def can_get_users(self, projects_names: set[str] | None, user_projects_names: set[str]) -> bool:
        """Проверка возможности получения списка пользователей"""
        decision = self.decide_list_users(
            requested_projects_names=projects_names,
            actor_projects_names=user_projects_names,
        )
        return decision is ListUsersDecision.ALLOWED

    def decide_update_user(
        self,
        target:  "User",
        *,
        change_admin: bool,
        change_status: bool,
        target_projects_names: set[str] | None,
        actor_projects_names: set[str] | None,
    ) -> UpdateUserDecision:
        """Решение о возможности обновления пользователя"""
        is_self_update = self.uuid == target.uuid

        if is_self_update: 
            if change_admin:
                return UpdateUserDecision.SELF_ADMIN_CHANGE_FORBIDDEN

            if change_status:
                return UpdateUserDecision.SELF_STATUS_CHANGE_FORBIDDEN

            return UpdateUserDecision.ALLOWED

        if actor_projects_names is None or target_projects_names is None: 
            return UpdateUserDecision. PROJECT_CONTEXT_MISSING

        if target_projects_names <= actor_projects_names:
            return UpdateUserDecision. ALLOWED

        return UpdateUserDecision.TARGET_PROJECT_NOT_OWNED

    def decide_list_users(
        self,
        *,
        requested_projects_names: set[str] | None,
        actor_projects_names:  set[str],
    ) -> ListUsersDecision:
        """Решение о возможности получения списка пользователей"""
        if not self.is_admin:
            return ListUsersDecision.NOT_ADMIN

        if requested_projects_names is not None and not requested_projects_names <= actor_projects_names:
            return ListUsersDecision.PROJECT_ACCESS_DENIED

        return ListUsersDecision.ALLOWED


# ==================== PROJECT ====================

@dataclass
class Project: 
    """
    Проект НИОКР.
    
    Администратор может:
    - Создавать проект
    - Редактировать параметры
    - Добавлять/удалять участников
    - Архивировать проект
    - Просматривать всю активность
    
    Пользователь может:
    - Видеть только назначенные ему проекты
    - Работать с этапами и записями
    """
    uuid: UUID
    name: str
    description: str | None
    creator:  User
    is_active: bool = True
    is_archived: bool = False
    is_blocked:  bool = False
    completed:  bool = False
    status: ProjectStatus = ProjectStatus. ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    start_date: str | None = None
    end_date: str | None = None

    def can_be_edited(self) -> bool:
        """Можно ли редактировать проект"""
        return not self.is_archived and not self.is_blocked

    def is_accessible(self) -> bool:
        """Доступен ли проект для работы"""
        return self. is_active and not self.is_blocked

    def archive(self) -> None:
        """Архивировать проект"""
        self.is_archived = True
        self.is_active = False
        self.status = ProjectStatus.ARCHIVED

    def block(self) -> None:
        """Заблокировать проект (например, при неоплате)"""
        self.is_blocked = True
        self.status = ProjectStatus.BLOCKED

    def unblock(self) -> None:
        """Разблокировать проект"""
        self.is_blocked = False
        if not self.is_archived:
            self.status = ProjectStatus. ACTIVE


# ==================== MEMBERSHIP ====================

@dataclass
class MemberShip:
    """
    Связь пользователя с проектом.
    
    Администратор может:
    - Добавлять участников в проект
    - Удалять участников из проекта
    - Деактивировать участника
    """
    uuid: UUID
    user: User
    project: Project
    joined_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    assigned_by: UUID | None = None

    def deactivate(self) -> None:
        """Деактивировать участие в проекте"""
        self. is_active = False


# ==================== STAGE ====================

@dataclass
class Stage: 
    """
    Этап проекта.
    
    Пользователь может:
    - Создавать этапы в своих проектах
    - Редактировать название этапа
    - Удалять/архивировать этапы
    """
    uuid: UUID
    name: str
    description: str
    creator: User
    project: Project
    completed: bool = False
    status:  StageStatus = StageStatus. ACTIVE
    created_at:  str = field(default_factory=lambda: datetime.now().isoformat())
    end_date: str | None = None
    order: int = 0

    def complete(self) -> None:
        """Отметить этап как завершенный"""
        self. completed = True
        self.status = StageStatus.COMPLETED

    def archive(self) -> None:
        """Архивировать этап"""
        self. status = StageStatus.ARCHIVED


# ==================== SUBSTAGE ====================

@dataclass
class SubStage:
    """
    Подэтап (работа) внутри этапа.
    
    Пользователь может:
    - Создавать подэтапы внутри этапа
    - Редактировать подэтапы
    - Удалять/архивировать подэтапы
    - Выбирать подэтап для ежедневной работы
    """
    uuid: UUID
    name: str
    description: str
    creator: User
    stage: Stage
    completed: bool = False
    status: StageStatus = StageStatus. ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    end_date: str | None = None
    order: int = 0

    def complete(self) -> None:
        """Отметить подэтап как завершенный"""
        self.completed = True
        self.status = StageStatus.COMPLETED

    def archive(self) -> None:
        """Архивировать подэтап"""
        self.status = StageStatus. ARCHIVED


# ==================== TASK ====================

@dataclass
class Task:
    """
    Задача в рамках подэтапа.
    
    Пользователь может: 
    - Создавать задачи
    - Редактировать задачи
    - Выбирать задачи для выполнения в конкретный день
    - Отмечать задачи как выполненные
    """
    uuid: UUID
    name: str
    description: str
    creator:  User
    substage: SubStage
    completed: bool = False
    status:  TaskStatus = TaskStatus.PENDING
    completion_dates: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def mark_completed(self, date: str) -> None:
        """Отметить задачу как выполненную в указанную дату"""
        self.completed = True
        self.status = TaskStatus.COMPLETED
        if date not in self.completion_dates:
            self.completion_dates.append(date)

    def mark_in_progress(self) -> None:
        """Отметить задачу как выполняемую"""
        self.status = TaskStatus.IN_PROGRESS

    def archive(self) -> None:
        """Архивировать задачу"""
        self.status = TaskStatus.ARCHIVED


# ==================== DAY ENTRY ====================

@dataclass
class DayEntry: 
    """
    Е��едневная запись пользователя.
    
    Пользователь может: 
    - Создавать запись на день
    - Выбирать подэтап дня
    - Выбирать задачи дня
    - Заполнять описание результатов
    - Прикреплять файлы
    - Заполнять таблицу
    - Использовать голосовой ввод
    
    Администратор может:
    - Просматривать записи всех пользователей
    - Фильтровать по периоду/пользователю/этапу
    """
    uuid: UUID
    date: str
    creator: User
    project: Project
    hours_spent: float = 0.0
    description: str = ""
    substage: SubStage | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def update_description(self, description: str) -> None:
        """Обновить описание результатов дня"""
        self.description = description
        self.updated_at = datetime.now().isoformat()

    def set_substage(self, substage: SubStage) -> None:
        """Установить подэтап дня"""
        self.substage = substage
        self.updated_at = datetime. now().isoformat()

    def update_hours(self, hours: float) -> None:
        """Обновить количество затраченных часов"""
        self.hours_spent = hours
        self.updated_at = datetime.now().isoformat()


# ==================== DAY TASK LINK ====================

@dataclass
class DayTaskLink:
    """
    Связь задачи с дневной записью.
    Задача может выполняться в несколько дней.
    """
    uuid: UUID
    day_entry: DayEntry
    task: Task
    completed_today: bool = False
    notes: str | None = None
    linked_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def mark_completed(self, notes: str | None = None) -> None:
        """Отметить задачу как выполненную в этот день"""
        self.completed_today = True
        if notes:
            self.notes = notes


# ==================== FILE ====================

@dataclass
class File:
    """
    Файл, прикрепленный к дневной записи.
    
    Пользователь может: 
    - Загружать один или несколько файлов
    - Прикреплять изображения
    - Просматривать превью изображений
    """
    uuid: UUID
    filename: str
    url: str
    day_entry: DayEntry
    uploader: User
    file_size: int = 0  # bytes
    file_type: str | None = None
    uploaded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_image(self) -> bool:
        """Проверка, является ли файл изображением"""
        image_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        return self.file_type in image_types if self.file_type else False


# ==================== TABLE ====================

@dataclass
class TableColumn:
    """Колонка таблицы"""
    uuid: UUID
    name: str
    data_type: str  # "text", "number", "date"
    order: int


@dataclass
class TableRow: 
    """Строка таблицы"""
    uuid: UUID
    order: int
    cells: dict[UUID, str] = field(default_factory=dict)  # column_uuid -> value


@dataclass
class Table:
    """
    Табличные данные дневной записи.
    
    Пользователь может: 
    - Добавлять/удалять колонки
    - Добавлять/удалять строки
    - Заполнять ячейки данными
    """
    uuid: UUID
    day_entry: DayEntry
    columns: list[TableColumn] = field(default_factory=list)
    rows: list[TableRow] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_column(self, name: str, data_type: str = "text") -> TableColumn:
        """Добавить колонку"""
        from uuid import uuid4
        new_column = TableColumn(
            uuid=uuid4(),
            name=name,
            data_type=data_type,
            order=len(self.columns)
        )
        self.columns.append(new_column)
        self.updated_at = datetime.now().isoformat()
        return new_column

    def add_row(self) -> TableRow:
        """Добавить строку"""
        from uuid import uuid4
        new_row = TableRow(
            uuid=uuid4(),
            order=len(self.rows),
            cells={}
        )
        self.rows.append(new_row)
        self.updated_at = datetime.now().isoformat()
        return new_row

    def update_cell(self, row_uuid: UUID, column_uuid: UUID, value: str) -> None:
        """Обновить значение ячейки"""
        for row in self.rows:
            if row.uuid == row_uuid:
                row.cells[column_uuid] = value
                self.updated_at = datetime.now().isoformat()
                break


# ==================== DRAFT ====================

@dataclass
class Draft:
    """
    Черновик дневной записи для автосохранения.
    
    Система может: 
    - Автоматически сохранять черновики
    - Восстанавливать данные при обновлении страницы
    """
    uuid: UUID
    content: dict  # JSON с произвольной структурой
    day_entry: DayEntry
    auto_saved: bool = True
    created_at: str = field(default_factory=lambda:  datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda:  datetime.now().isoformat())

    def update_content(self, content: dict) -> None:
        """Обновить содержимое черновика"""
        self.content = content
        self.updated_at = datetime.now().isoformat()


# ==================== VOICE RECORD ====================

@dataclass
class VoiceRecord:
    """
    Голосовая запись для ввода описания.
    
    Пользователь может:
    - Записывать голос
    - Получать текст распознавания
    - Редактировать распознанный текст
    """
    uuid: UUID
    day_entry: DayEntry
    audio_file_url: str
    transcription: str | None = None
    status: TranscriptionStatus = TranscriptionStatus.PENDING
    duration_seconds: float = 0.0
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def set_transcription(self, text: str) -> None:
        """Установить результат распознавания"""
        self.transcription = text
        self.status = TranscriptionStatus.COMPLETED

    def mark_failed(self) -> None:
        """Отметить как неудачное распознавание"""
        self. status = TranscriptionStatus. FAILED


# ==================== SUBSCRIPTION ====================

@dataclass
class Subscribe:
    """
    Подписка проекта. 
    
    Администратор может:
    - Просматривать статус подписки
    - Инициировать оплату
    - Просматривать историю платежей
    
    Система должна:
    - Ограничивать функционал при неоплате
    - Отслеживать срок действия
    """
    uuid: UUID
    project: Project
    plan_type: str  # "trial", "basic", "premium", etc.
    status: SubscriptionStatus = SubscriptionStatus. TRIAL
    start_date: str = field(default_factory=lambda:  datetime.now().isoformat())
    end_date: str | None = None
    auto_renew: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_active(self) -> bool:
        """Проверка активности подписки"""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.end_date:
            return datetime.now() <= datetime.fromisoformat(self. end_date)
        return True

    def get_features_limit(self) -> dict: 
        """Ограничения функционала в зависимости от статуса"""
        if self.status == SubscriptionStatus.ACTIVE and self.is_active():
            return {
                "can_export":  True,
                "can_add_users": True,
                "can_add_projects": True,
                "max_users": 100,
                "max_projects":  50,
                "read_only":  False,
            }
        elif self.status == SubscriptionStatus.TRIAL: 
            return {
                "can_export": True,
                "can_add_users": True,
                "can_add_projects": True,
                "max_users": 5,
                "max_projects":  1,
                "read_only":  False,
            }
        else:  # EXPIRED or CANCELLED
            return {
                "can_export": False,
                "can_add_users":  False,
                "can_add_projects": False,
                "read_only": True,
            }

    def expire(self) -> None:
        """Пометить подписку как истекшую"""
        self.status = SubscriptionStatus.EXPIRED

    def cancel(self) -> None:
        """Отменить подписку"""
        self. status = SubscriptionStatus. CANCELLED
        self.auto_renew = False

    def renew(self, end_date: str) -> None:
        """Продлить подписку"""
        self.status = SubscriptionStatus.ACTIVE
        self.end_date = end_date


# ==================== PAYMENT ====================

@dataclass
class Payment: 
    """
    Платеж за подписку.
    
    Администратор может:
    - Просматривать историю платежей
    - Скачивать чеки и счета
    """
    uuid: UUID
    subscription: Subscribe
    amount: float
    currency: str = "RUB"
    status: PaymentStatus = PaymentStatus. PENDING
    payment_date: str | None = None
    invoice_url: str | None = None
    receipt_url: str | None = None
    payment_method: str | None = None  # "card", "invoice", "wire_transfer"
    created_at: str = field(default_factory=lambda:  datetime.now().isoformat())

    def complete(self, receipt_url: str | None = None) -> None:
        """Отметить платеж как завершенный"""
        self.status = PaymentStatus.COMPLETED
        self.payment_date = datetime.now().isoformat()
        if receipt_url:
            self. receipt_url = receipt_url

    def fail(self) -> None:
        """Отметить платеж как неудачный"""
        self.status = PaymentStatus.FAILED

    def refund(self) -> None:
        """Возврат платежа"""
        self.status = PaymentStatus.REFUNDED


# ==================== REPORT ====================

@dataclass
class Report:
    """
    Отчет в формате PDF.
    
    Пользователь может:
    - Выгружать свой отчет за период
    
    Администратор может:
    - Выгружать отчет любого пользователя
    - Выгружать сводный отчет по проекту
    - Фильтровать по периоду/этапу/подэтапу
    """
    uuid: UUID
    project:  Project
    generated_by: User
    target_user: User | None = None  # None = сводный отчет по всем
    start_date: str = ""
    end_date: str = ""
    file_path: str | None = None
    status: ReportStatus = ReportStatus.PENDING
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_user_report(self) -> bool:
        """Отчет по конкретному пользователю"""
        return self.target_user is not None

    def is_summary_report(self) -> bool:
        """Сводный отчет по всем пользователям проекта"""
        return self. target_user is None

    def mark_completed(self, file_path: str) -> None:
        """Отметить отчет как сформированный"""
        self.status = ReportStatus.COMPLETED
        self.file_path = file_path

    def mark_failed(self) -> None:
        """Отметить отчет как неудачный"""
        self.status = ReportStatus.FAILED


# ==================== AUDIT LOG ====================

@dataclass
class AuditLog:
    """
    Журнал аудита действий пользователей.
    
    Система должна:
    - Логировать все важные действия
    - Особенно вход и экспорт отчетов
    """
    uuid: UUID
    user: User
    action: AuditAction
    entity_type: str  # "Project", "User", "Report", "DayEntry", etc.
    entity_id: UUID | None = None
    details: dict = field(default_factory=dict)  # Дополнительная информация
    ip_address: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_detail(self, key: str, value: any) -> None:
        """Добавить деталь в лог"""
        self.details[key] = value