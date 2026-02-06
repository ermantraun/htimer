from __future__ import annotations
from uuid import UUID
from datetime import date
from enum import Enum
import sqlalchemy as sq
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

# ======= BASE =======
class Base(DeclarativeBase):
    pass

# ======= ENUMS =======
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

# ======= USER =======
class User(Base):
    __tablename__ = "users"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    email: Mapped[str] = mapped_column(sq.String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(sq.Enum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(sq.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    last_login: Mapped[date | None] = mapped_column(sq.Date, nullable=True)
    creator_uuid: Mapped[UUID | None] = mapped_column(
        sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=True
    )

    owned_projects: Mapped[list[Project]] = relationship("Project", back_populates="creator", cascade="all, delete-orphan")
    memberships: Mapped[list[MemberShip]] = relationship("MemberShip", back_populates="user", cascade="all, delete-orphan")
    stages: Mapped[list[Stage]] = relationship("Stage", back_populates="creator", cascade="all, delete-orphan")
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="creator", cascade="all, delete-orphan")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="creator", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="subscription_user", cascade="all, delete-orphan")

    creator: Mapped[User | None] = relationship(
        "User", remote_side="User.uuid", back_populates="created_users"
    )
    created_users: Mapped[list[User]] = relationship(
        "User", back_populates="creator", cascade="all, delete-orphan"
    )

# ======= PROJECT =======
class Project(Base):
    __tablename__ = "projects"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sq.String(1000), nullable=True)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    creator: Mapped[User] = relationship("User", back_populates="owned_projects")

    start_date: Mapped[date | None] = mapped_column(sq.Date)
    end_date: Mapped[date | None] = mapped_column(sq.Date)
    status: Mapped[ProjectStatus] = mapped_column(sq.Enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE)
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)

    stages: Mapped[list[Stage]] = relationship("Stage", back_populates="project", cascade="all, delete-orphan")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="project", cascade="all, delete-orphan")
    subscription: Mapped[Subscription | None] = relationship("Subscription", back_populates="project", uselist=False, cascade="all, delete-orphan")
    memberships: Mapped[list[MemberShip]] = relationship("MemberShip", back_populates="project", cascade="all, delete-orphan")


# ======= MEMBER / ASSOCIATION =======
class MemberShip(Base):
    __tablename__ = "memberships"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    user_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"), primary_key=True)
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    assigned_by: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))

    user: Mapped[User] = relationship("User", back_populates="memberships")
    project: Mapped[Project] = relationship("Project", back_populates="memberships")


# ======= SUBSCRIPTION =======
class Subscription(Base):
    __tablename__ = "subscriptions"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"), nullable=False, unique=True)
    project: Mapped[Project] = relationship("Project", back_populates="subscription")
    
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    auto_renew: Mapped[bool] = mapped_column(sq.Boolean, default=True)
    start_date: Mapped[date | None] = mapped_column(sq.Date)
    end_date: Mapped[date | None] = mapped_column(sq.Date)
    status: Mapped[SubscriptionStatus] = mapped_column(sq.Enum(SubscriptionStatus), default=SubscriptionStatus.UNACTIVE)


# ======= PAYMENT =======
class Payment(Base):
    __tablename__ = "payments"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    subscription_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("subscriptions.uuid", ondelete="CASCADE"), nullable=False)
    subscription: Mapped[Subscription] = relationship("Subscription", back_populates="payments")
    
    amount: Mapped[float] = mapped_column(sq.Float, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(sq.Enum(CurrencyEnum), nullable=False, default=CurrencyEnum.RUB)
    status: Mapped[PaymentStatus] = mapped_column(sq.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(sq.Enum(PaymentMethod))
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)


# ======= STAGE =======
class Stage(Base):
    __tablename__ = "stages"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sq.String(1000))
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="stages")
    project_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"))
    project: Mapped[Project] = relationship("Project", back_populates="stages")

    parent_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey("stages.uuid"))
    parent: Mapped[Stage | None] = relationship("Stage", remote_side="Stage.uuid", back_populates="children")
    children: Mapped[list[Stage]] = relationship("Stage", back_populates="parent", cascade="all, delete-orphan")

    tasks: Mapped[list[Task]] = relationship("Task", back_populates="substage", cascade="all, delete-orphan")
    daily_logs: Mapped[list[DailyLog]] = relationship("DailyLog", back_populates="substage", cascade="all, delete-orphan")

    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    main_path: Mapped[bool] = mapped_column(sq.Boolean, nullable=False, default=False)
    status: Mapped[StageStatus] = mapped_column(sq.Enum(StageStatus), default=StageStatus.ACTIVE)


# ======= TASK =======
class Task(Base):
    __tablename__ = "tasks"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sq.String(1000))
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="tasks")
    
    substage_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("stages.uuid", ondelete="CASCADE"))
    substage: Mapped[Stage] = relationship("Stage", back_populates="tasks")
    
    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(sq.Enum(TaskStatus), default=TaskStatus.PENDING)
    completion_date: Mapped[date | None] = mapped_column(sq.Date)
    working_days: Mapped[list[date]] = mapped_column(ARRAY(sq.Date), default=[])


# ======= DAILY LOG =======
class DailyLog(Base):
    __tablename__ = "daily_logs"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    
    creator_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("users.uuid", ondelete="CASCADE"))
    creator: Mapped[User] = relationship("User", back_populates="daily_logs")
    
    project_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("projects.uuid", ondelete="CASCADE"))
    project: Mapped[Project] = relationship("Project", back_populates="daily_logs")
    
    substage_uuid: Mapped[UUID | None] = mapped_column(sq.ForeignKey("stages.uuid"))
    substage: Mapped[Stage | None] = relationship("Stage", back_populates="daily_logs")

    files: Mapped[list[File]] = relationship("File", back_populates="daily_log", cascade="all, delete-orphan")

    created_at: Mapped[date] = mapped_column(sq.Date, nullable=False)
    updated_at: Mapped[date | None] = mapped_column(sq.Date)
    draft: Mapped[bool] = mapped_column(sq.Boolean, default=False)
    hours_spent: Mapped[float] = mapped_column(sq.Float, default=0.0)
    description: Mapped[str] = mapped_column(sq.String(2000), default="")


# ======= FILE =======
class File(Base):
    __tablename__ = "files"

    uuid: Mapped[UUID] = mapped_column(sq.UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    uri: Mapped[str] = mapped_column(sq.String(255), nullable=False)
    uploaded_at: Mapped[date] = mapped_column(sq.Date, nullable=False)

    daily_log_uuid: Mapped[UUID] = mapped_column(sq.ForeignKey("daily_logs.uuid", ondelete="CASCADE"))
    daily_log: Mapped[DailyLog] = relationship("DailyLog", back_populates="files")
