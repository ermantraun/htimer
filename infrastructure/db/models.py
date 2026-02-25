from __future__ import annotations
from uuid import UUID
from datetime import date
from enum import Enum
import sqlalchemy as sq
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY


class Base(DeclarativeBase):
    pass

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"

class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    BLOCKED = "blocked"
    COMPLETED = "completed"

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

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"

class CurrencyEnum(str, Enum):
    RUB = "RUB"

class StageStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ReportStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


def get_enum_values(enum_cls: type[Enum]) -> list[str]:
    return [e.value for e in enum_cls]

class User(Base):
    __tablename__ = "users"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    email: Mapped[str] = mapped_column(sq.String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(sq.Enum(UserRole, values_callable=get_enum_values), nullable=False,)
    status: Mapped[UserStatus] = mapped_column(sq.Enum(UserStatus, values_callable=get_enum_values), nullable=False, default=UserStatus.ACTIVE)
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    last_login: Mapped[date | None] = mapped_column(sq.Date, nullable=True)
    creator_uuid: Mapped[UUID | None] = mapped_column(
        sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=True
    )

    owned_projects: Mapped[list[Project]] = relationship("Project", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    memberships: Mapped[list[MemberShip]] = relationship("MemberShip", back_populates="user", cascade="all, delete-orphan", foreign_keys="[MemberShip.user_uuid]", passive_deletes=True, lazy="raise")
    assigned_memberships: Mapped[list[MemberShip]] = relationship("MemberShip", back_populates="assigned_by_user", cascade="all, delete-orphan", foreign_keys="[MemberShip.assigned_by_uuid]", passive_deletes=True, lazy="raise")
    stages: Mapped[list[Stage]] = relationship("Stage", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    reports: Mapped[list[Report]] = relationship("Report", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")


    creator: Mapped[User | None] = relationship(
        "User", remote_side="User.uuid", back_populates="created_users", lazy="raise")
    created_users: Mapped[list[User]] = relationship(
        "User", back_populates="creator", cascade="all, delete-orphan", passive_deletes=True, lazy="raise"
    )
    
    __table_args__ = (
        sq.UniqueConstraint("email", name="uq_users_email"),
        sq.CheckConstraint(
            "(role = 'admin') OR (role = 'user' and creator_uuid IS NOT NULL)",
            name="check_user_creator_for_user_role",
        ),
    )


class Project(Base):
    __tablename__ = "projects"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sq.String(1000), nullable=True)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    creator: Mapped[User] = relationship("User", back_populates="owned_projects", lazy="raise")

    start_date: Mapped[date | None] = mapped_column(sq.Date)
    end_date: Mapped[date | None] = mapped_column(sq.Date)
    status: Mapped[ProjectStatus] = mapped_column(sq.Enum(ProjectStatus, values_callable=get_enum_values), nullable=False, default=ProjectStatus.ACTIVE)
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)

    stages: Mapped[list[Stage]] = relationship("Stage", back_populates="project", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="project", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    subscription: Mapped[Subscription | None] = relationship("Subscription", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="raise")
    memberships: Mapped[list[MemberShip]] = relationship("MemberShip", back_populates="project", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")

    __table_args__ = (
        sq.UniqueConstraint("creator_uuid", "name", name="uq_projects_creator_name"),
        sq.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="check_project_start_end_dates",
        ),
    )


class MemberShip(Base):
    __tablename__ = "memberships"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    user_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"))
    joined_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    assigned_by_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))

    user: Mapped[User] = relationship("User", back_populates="memberships", foreign_keys=[user_uuid], lazy="raise")
    project: Mapped[Project] = relationship("Project", back_populates="memberships", lazy="raise")
    assigned_by_user: Mapped[User] = relationship("User", foreign_keys=[assigned_by_uuid], lazy="raise")

    
    __table_args__ = (
        sq.UniqueConstraint("project_uuid", "user_uuid", name="uq_memberships_user_project"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"), nullable=False)
    project: Mapped[Project] = relationship("Project", back_populates="subscription", lazy="raise")
    
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    start_date: Mapped[date | None] = mapped_column(sq.Date)
    end_date: Mapped[date | None] = mapped_column(sq.Date)
    status: Mapped[SubscriptionStatus] = mapped_column(sq.Enum(SubscriptionStatus, values_callable=get_enum_values), default=SubscriptionStatus.UNACTIVE)

    __table_args__ = (
        sq.UniqueConstraint("project_uuid", name="uq_subscriptions_project_uuid"),
        sq.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="check_subscription_start_end_dates",
        ),
    )


class Payment(Base):
    __tablename__ = "payments"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    subscription_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("subscriptions.uuid", ondelete="CASCADE"), nullable=False)
    subscription: Mapped[Subscription] = relationship("Subscription", back_populates="payments", lazy="raise")
    
    amount: Mapped[float] = mapped_column(sq.Float, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(sq.Enum(CurrencyEnum, values_callable=get_enum_values), nullable=False, default=CurrencyEnum.RUB)
    status: Mapped[PaymentStatus] = mapped_column(sq.Enum(PaymentStatus, values_callable=get_enum_values), nullable=False, default=PaymentStatus.PENDING)
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    complete_date: Mapped[date | None] = mapped_column(sq.Date)
    applied_to_subscription: Mapped[bool] = mapped_column(sq.Boolean, default=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(sq.String(255))

    __table_args__ = (
        sq.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )


class Stage(Base):
    __tablename__ = "stages"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sq.String(1000))
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="stages", lazy="raise")
    project_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"))
    project: Mapped[Project] = relationship("Project", back_populates="stages", lazy="raise")

    parent_uuid: Mapped[UUID | None] = mapped_column(
        sq.ForeignKey('stages.uuid', ondelete='CASCADE'),
        nullable=True,
        comment='Родительский этап'
    )
    parent: Mapped[Stage | None] = relationship("Stage", remote_side="Stage.uuid", back_populates="children", lazy="raise")
    children: Mapped[list[Stage]] = relationship("Stage", back_populates="parent", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")

    tasks: Mapped[list[Task]] = relationship("Task", back_populates="substage", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="substage", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")

    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    main_path: Mapped[bool] = mapped_column(sq.Boolean, nullable=False, default=False)
    status: Mapped[StageStatus] = mapped_column(sq.Enum(StageStatus, values_callable=get_enum_values), default=StageStatus.ACTIVE)

    __table_args__ = (
        sq.UniqueConstraint("parent_uuid", "name", name="uq_parent_name"),
        sq.UniqueConstraint("parent_uuid", "main_path", name="uq_parent_main_path")
    )


class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sq.String(1000), nullable=False)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="tasks", lazy="raise")
    
    substage_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("stages.uuid", ondelete="CASCADE"))
    substage: Mapped[Stage] = relationship("Stage", back_populates="tasks", lazy="raise")
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(sq.Enum(TaskStatus, values_callable=get_enum_values), default=TaskStatus.PENDING)
    completion_date: Mapped[date | None] = mapped_column(sq.Date)
    working_days: Mapped[list[date]] = mapped_column(ARRAY(sq.Date), default=[])

    __table_args__ = (
        
        sq.UniqueConstraint("substage_uuid", "name", name="uq_substage_name"),
        
        
        
# """         sq.CheckConstraint(
#             "array_length(working_days, 1) = cardinality(ARRAY(SELECT DISTINCT unnest(working_days)))",
#             name="ck_tasks_working_days_unique",
#         ),
#         sq.CheckConstraint(
#             "completion_date IS NULL OR completion_date = ANY(working_days)",
#             name="ck_tasks_completion_date_in_working_days",
#         ), """
    )


class DailyLog(Base):
    __tablename__ = "daily_logs"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="daily_logs", lazy="raise")
    
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"))
    project: Mapped[Project] = relationship("Project", back_populates="daily_logs", lazy="raise")
    
    substage_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey("stages.uuid"))
    substage: Mapped[Stage | None] = relationship("Stage", back_populates="daily_logs", lazy="raise")

    files: Mapped[list[File]] = relationship("File", back_populates="daily_log", cascade="all, delete-orphan", passive_deletes=True, lazy="raise")

    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    updated_at: Mapped[date | None] = mapped_column(sq.Date)
    draft: Mapped[bool] = mapped_column(sq.Boolean, default=False)
    hours_spent: Mapped[float] = mapped_column(sq.Float, default=0.0)
    description: Mapped[str] = mapped_column(sq.String(2000), default="")

    __table_args__ = (
        sq.UniqueConstraint(
            "creator_uuid", "project_uuid", "created_at", name="uq_creator_project_dailylog_date"
        ),
    )


class File(Base):
    __tablename__ = "files"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    uri: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    uploaded_at: Mapped[date] = mapped_column(sq.Date, nullable=False)

    daily_log_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("daily_logs.uuid", ondelete="CASCADE"))
    daily_log: Mapped[DailyLog] = relationship("DailyLog", back_populates="files", lazy="raise")

    __table_args__ = (
        sq.UniqueConstraint("daily_log_uuid", "name", name="uq_daily_log_name"),
    )


class UserReport(Base):
    __tablename__ = "user_reports"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship("User", lazy="raise")
    report_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("reports.uuid", ondelete="CASCADE"), nullable=False)
    report: Mapped[Report] = relationship("Report", lazy="raise", back_populates="target_users")

# class Report:
#     uuid: UUID
#     project: Project
#     generated_by: User
#     generated_at: date
#     target_users: list[User] | None = None
#     start_date: date | None = None
#     end_date: date | None = None   
#     file_path: str | None = None
#     status: ReportStatus = ReportStatus.PENDING
class Report(Base):
    __tablename__ = "reports"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"), nullable=False)
    project: Mapped[Project] = relationship("Project", lazy="raise", back_populates="reports")
    
    generated_by_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    creator: Mapped[User] = relationship("User", lazy="raise", back_populates="reports")
    target_users: Mapped[list[User]] = relationship("User", secondary="user_reports", lazy="raise", cascade="all, delete-orphan", passive_deletes=True)

    generated_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    start_date: Mapped[date | None] = mapped_column(sq.Date)
    end_date: Mapped[date | None] = mapped_column(sq.Date)
    file_path: Mapped[str | None] = mapped_column(sq.String(255))
    status: Mapped[ReportStatus] = mapped_column(sq.Enum(ReportStatus, values_callable=get_enum_values), default=ReportStatus.PENDING)
