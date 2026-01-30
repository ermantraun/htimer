from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import sqlalchemy as sq
from uuid import UUID
from enum import Enum
from datetime import date



class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    
class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"
        
    
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Имя пользователя')
    email: Mapped[str] = mapped_column(sq.String(100), nullable=False, comment='Почта пользователя')
    password_hash: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Хэш пароля пользователя')
    creator_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey('users.uuid', ondelete='CASCADE'), comment='Создатель пользователя', nullable=True, unique=True)
    
    creator: Mapped["User"] = relationship('User', back_populates='created_users', foreign_keys='User.uuid', remote_side='User.creator_uuid', lazy="raise")
    created_users: Mapped[list["User"]] = relationship('User', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='creator')

    projects: Mapped[list["Project"]] = relationship('Project', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='creator')

    payments: Mapped[list["Payment"]] = relationship('Payment', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='subscription')
    
    stages: Mapped[list["Stage"]] = relationship('Stage', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='creator')


    daily_logs: Mapped[list["DailyLog"]] = relationship('DailyLog', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='creator')

    tasks: Mapped[list["Task"]] = relationship('Task', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='creator')

    role: Mapped[UserRole] = mapped_column(sq.Enum(UserRole), nullable=False, comment='Роль пользователя')
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания пользователя')
    status: Mapped[UserStatus] = mapped_column(sq.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE, comment='Статус пользователя')
    last_login: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата последнего входа пользователя')
    
    __table_args__ = (
        sq.CheckConstraint("role == 'admin' OR role == 'user' and creator_uuid IS NOT NULL", name='check_user_creator_for_user_role'),
    )
    

""" class Project:
    uuid: UUID
    name: str
    description: str | None
    creator: User
    created_at: date
    status: ProjectStatus = ProjectStatus.ACTIVE
    start_date: date | None = None
    end_date: date | None = None  """

class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"
    COMPLETED = "completed"

class Project(Base):
    __tablename__ = "projects"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Название проекта')
    description: Mapped[str | None] = mapped_column(sq.String(1000), nullable=True, comment='Описание проекта')
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False, comment='Создатель проекта')
    creator: Mapped["User"] = relationship('User', back_populates='projects', foreign_keys='User.uuid',)

    daily_logs: Mapped[list["DailyLog"]] = relationship('DailyLog', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='project')
    
    subscription: Mapped["Subscription"] = relationship('Subscription', cascade='all, delete-orphan', passive_deletes=True, back_populates='project', foreign_keys='Subscription.project_uuid')

    stages: Mapped[list["Stage"]] = relationship('Stage', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='project')
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания проекта')
    status: Mapped[ProjectStatus] = mapped_column(sq.Enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE, comment='Статус проекта')
    start_date: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата начала проекта')
    end_date: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата окончания проекта')
    
    __table_args__ = (
        sq.UniqueConstraint('creator_uuid', 'name', name='uq_creator_project_name'),
        sq.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name='check_project_start_end_dates'),
    )
    
# class Subscription:
#     uuid: UUID
#     project: Project
#     created_at: date
#     auto_renew: bool = True
#     start_date: date | None = None
#     end_date: date | None = None
#     status: SubscriptionStatus = SubscriptionStatus.UNACTIVE

class SubscriptionStatus(Enum):
    ACTIVE = "active"
    UNACTIVE = "unactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    
class Subscription(Base):
    __tablename__ = "subscriptions"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
     
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=False, comment='Проект подписки', unique=True)
    project: Mapped["Project"] = relationship('Project', back_populates='subscription', foreign_keys='Project.uuid',)
    
    payments: Mapped[list["Payment"]] = relationship('Payment', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='subscription')
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания подписки')
    auto_renew: Mapped[bool] = mapped_column(sq.Boolean, nullable=False, default=True, comment='Автопродление подписки')
    start_date: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата начала подписки')
    end_date: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата окончания подписки')
    status: Mapped[SubscriptionStatus] = mapped_column(sq.Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.UNACTIVE, comment='Статус подписки')
    
    __table_args__ = (
        sq.CheckConstraint('start_date IS NULL OR end_date IS NULL OR start_date <= end_date', name='check_subscription_start_end_dates'),
    )

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    
class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"
    
class CurrencyEnum(str, Enum):
    RUB = "RUB"    
    
class Payment(Base):
    __tablename__ = "payments"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    subscription_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('subscriptions.uuid', ondelete='CASCADE'), nullable=False, comment='Подписка платежа')
    subscription: Mapped["Subscription"] = relationship('Subscription', back_populates='payments', foreign_keys='Subscription.uuid',)
    
    amount: Mapped[float] = mapped_column(sq.Float, nullable=False, comment='Сумма платежа')
    currency: Mapped[CurrencyEnum] = mapped_column(sq.Enum(CurrencyEnum), nullable=False, default=CurrencyEnum.RUB, comment='Валюта платежа')
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания платежа')
    status: Mapped[PaymentStatus] = mapped_column(sq.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, comment='Статус платежа')
    payment_date: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата проведения платежа')
    payment_method: Mapped[PaymentMethod | None] = mapped_column(sq.Enum(PaymentMethod), nullable=True, comment='Метод оплаты платежа')
    
    __table_args__ = (
        sq.CheckConstraint("amount >= 0", name="ck_payment_amount_positive"),
    )


class StageStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Stage(Base):
    __tablename__ = "stages"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Название этапа')
    description: Mapped[str | None] = mapped_column(sq.String(1000), nullable=True, comment='Описание этапа')
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False, comment='Создатель этапа')
    creator: Mapped["User"] = relationship('User', foreign_keys='User.uuid', back_populates='stages')
    
    project_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey('projects.uuid', ondelete='CASCADE'), comment='Проект этапа')
    project: Mapped["Project"] = relationship('Project', foreign_keys='Project.uuid', back_populates='stages')
    
    daily_logs: Mapped[list["DailyLog"]] = relationship('DailyLog', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='substage')

    
    tasks: Mapped[list["Task"]] = relationship('Task', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='substage')
    
    
    parent_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey('stages.uuid', ondelete='DELETE'), nullable=True, comment='Родительский этап', unique=True)
    parent: Mapped["Stage"] = relationship('Stage', remote_side=[uuid], foreign_keys='Stage.uuid')
    children: Mapped[list["Stage"]] = relationship('Stage', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True, back_populates='parent', foreign_keys='Stage.parent_uuid')
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания этапа')
    main_path: Mapped[bool] = mapped_column(sq.Boolean, nullable=False, comment='Основной путь этапа')
    status: Mapped[StageStatus] = mapped_column(sq.Enum(StageStatus), nullable=False, default=StageStatus.ACTIVE, comment='Статус этапа')
    
    
    __table_args__ = (
        sq.CheckConstraint("main_path OR parent_uuid IS NOT NULL", name="ck_stage_main_path_boolean"),
    )
    
    
# class DailyLog:
#     uuid: UUID
#     creator: User
#     project: Project
#     created_at: date
#     draft: bool = False
#     updated_at: date | None = None
#     hours_spent: float = 0.0
#     description: str = ""
#     substage: Stage | None = None    
    
class DailyLog(Base):
    __tablename__ = "daily_logs"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False, comment='Создатель дневного отчета')
    creator: Mapped["User"] = relationship('User', foreign_keys='User.uuid', back_populates='daily_logs')
    
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('projects.uuid', ondelete='CASCADE'), nullable=False, comment='Проект дневного отчета')
    project: Mapped["Project"] = relationship('Project', foreign_keys='Project.uuid', back_populates='daily_logs')
     
    substage_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey('stages.uuid', ondelete='CASCADE'), nullable=True, comment='Подэтап дневного отчета')
    substage: Mapped["Stage"] = relationship('Stage', foreign_keys='Stage.uuid', back_populates='daily_logs')
    
    files: Mapped['File'] = relationship('File', cascade='all, delete-orphan', lazy='dynamic', passive_deletes=True, comment='Привязанные файлы')
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания дневного отчета')
    draft: Mapped[bool] = mapped_column(sq.Boolean, nullable=False, default=False, comment='Черновик дневного отчета')
    updated_at: Mapped[date | None] = mapped_column(sq.Date, nullable=True, comment='Дата обновления дневного отчета')
    hours_spent: Mapped[float] = mapped_column(sq.Float, nullable=False, default=0.0, comment='Количество часов, затраченных в дневном отчете')
    description: Mapped[str] = mapped_column(sq.String(2000), nullable=False, default="", comment='Описание дневного отчета')
    
    __table_args__ = (
        sq.UniqueConstraint('creator_uuid', 'project_uuid', 'created_at', name='uq_creator_project_dailylog_date'),
    )
    
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    
class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Название задачи')
    description: Mapped[str | None] = mapped_column(sq.String(1000), nullable=True, comment='Описание задачи')
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('users.uuid', ondelete='CASCADE'), nullable=False, comment='Создатель задачи')
    creator: Mapped["User"] = relationship('User', foreign_keys='User.uuid', back_populates='tasks')
    
    substage_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey('stages.uuid', ondelete='CASCADE'), nullable=False, comment='Подэтап задачи')
    substage: Mapped["Stage"] = relationship('Stage', foreign_keys='Stage.uuid', back_populates='tasks')
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата создания задачи')
        
    status: Mapped[TaskStatus] = mapped_column(sq.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, comment='Статус задачи')
    
    # completion_dates: Mapped[str] = mapped_column(sq.String(1000), nullable=False, comment='Даты завершения задачи в формате JSON')
    

    # working_days: Mapped[list[sq.Date]] = mapped_column(
    #     pdialects.ARRAY(date),
    #     nullable=False,
    #     server_default="{}",
    # )

    # __table_args__ = (
    #     sq.CheckConstraint(
    #         """
    #         array_length(working_days, 1)
    #         =
    #         cardinality(
    #             ARRAY(
    #                 SELECT DISTINCT unnest(solved_days)
    #             )
    #         )
    #         """,
    #         name="ck_tasks_solved_days_unique"
    #     ),
    # )
    
class File(Base):
    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='Название файла')
    uri: Mapped[str] = mapped_column(sq.String(255), nullable=False, comment='URI файла')
    uploaded_at: Mapped[date] = mapped_column(sq.Date, nullable=False, comment='Дата загрузки')
    
    daily_log_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey(column='dailylogs.uuid', ondelete='CASCADE'), nullable=False, comment='uuid целевой записи дня')
    daily_log: Mapped[DailyLog] = relationship('DailyLog', foreign_keys='DailyLog.uuid', back_populates='files')    
        