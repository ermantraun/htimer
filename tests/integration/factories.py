from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID, uuid4

from htimer.domain import entities, value_objects
from htimer.infrastructure.db import models
from sqlalchemy.ext.asyncio import AsyncSession


def _unique_str(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _today(offset_days: int = 0) -> date:
    return date.today() + timedelta(days=offset_days)


# -------------------- Domain entities --------------------

def make_user_entity(
    *,
    role: entities.UserRole = entities.UserRole.ADMIN,
    creator: entities.User | None = None,
    email: str | None = None,
    name: str | None = None,
    uuid: UUID | None = None,
) -> entities.User:
    return entities.User(
        uuid=uuid or uuid4(),
        name=name or _unique_str("user"),
        email=email or f"{_unique_str('user')}@example.com",
        password_hash="hashed",
        creator=creator,  # type: ignore[arg-type]
        role=role,
        created_at=_today(),
        status=entities.UserStatus.ACTIVE,
        last_login=None,
    )


def make_project_entity(
    *,
    creator: entities.User,
    name: str | None = None,
    uuid: UUID | None = None,
) -> entities.Project:
    return entities.Project(
        uuid=uuid or uuid4(),
        name=name or _unique_str("project"),
        description="desc",
        creator=creator,
        created_at=_today(),
        status=entities.ProjectStatus.ACTIVE,
        start_date=None,
        end_date=None,
    )


def make_stage_entity(
    *,
    creator: entities.User,
    project: entities.Project,
    parent: entities.Stage | None = None,
    name: str | None = None,
    main_path: bool | None = None,
    uuid: UUID | None = None,
) -> entities.Stage:
    return entities.Stage(
        uuid=uuid or uuid4(),
        name=name or _unique_str("stage"),
        description="desc",
        creator=creator,
        created_at=_today(),
        project=project,
        parent=parent,
        main_path=main_path,
        status=entities.StageStatus.ACTIVE,
    )


def make_daily_log_entity(
    *,
    creator: entities.User,
    project: entities.Project,
    substage: entities.Stage | None = None,
    uuid: UUID | None = None,
) -> entities.DailyLog:
    return entities.DailyLog(
        uuid=uuid or uuid4(),
        creator=creator,
        project=project,
        created_at=_today(),
        draft=False,
        updated_at=None,
        hours_spent=2.5,
        description="work",
        substage=substage,
    )


def make_task_entity(
    *,
    creator: entities.User,
    substage: entities.Stage,
    name: str | None = None,
    uuid: UUID | None = None,
) -> entities.Task:
    return entities.Task(
        uuid=uuid or uuid4(),
        name=name or _unique_str("task"),
        description="desc",
        creator=creator,
        created_at=_today(),
        substage=substage,
        status=entities.TaskStatus.PENDING,
        working_dates=frozenset({_today()}),
        completion_date=None,
    )


def make_subscription_entity(
    *,
    project: entities.Project,
    uuid: UUID | None = None,
) -> entities.Subscription:
    return entities.Subscription(
        uuid=uuid or uuid4(),
        project=project,
        created_at=_today(),
        auto_renew=True,
        start_date=_today(),
        end_date=_today(30),
        status=entities.SubscriptionStatus.UNACTIVE,
    )


def make_payment_entity(
    *,
    subscription: entities.Subscription,
    uuid: UUID | None = None,
) -> entities.Payment:
    return entities.Payment(
        uuid=uuid or uuid4(),
        subscription=subscription,
        amount=value_objects.MoneyAmount(amount=100.0),
        created_at=_today(),
        status=entities.PaymentStatus.PENDING,
        complete_date=None,
    )


def make_membership_entity(
    *,
    user: entities.User,
    project: entities.Project,
    assigned_by: entities.User,
    uuid: UUID | None = None,
) -> entities.MemberShip:
    return entities.MemberShip(
        uuid=uuid or uuid4(),
        user=user,
        project=project,
        joined_at=_today(),
        assigned_by=assigned_by,
    )


def make_file_entity(
    *,
    daily_log: entities.DailyLog,
    filename: str | None = None,
    uri: str | None = None,
    uuid: UUID | None = None,
) -> entities.DailyLogFile:
    return entities.DailyLogFile(
        uuid=uuid or uuid4(),
        filename=filename or _unique_str("file"),
        uri=uri or f"s3://bucket/{_unique_str('file')}",
        daily_log=daily_log,
        uploaded_at=_today(),
    )


# -------------------- ORM models --------------------

def build_user_model(
    *,
    role: models.UserRole = models.UserRole.ADMIN,
    creator: models.User | None = None,
    email: str | None = None,
    name: str | None = None,
    uuid: UUID | None = None,
) -> models.User:
    return models.User(
        uuid=uuid or uuid4(),
        name=name or _unique_str("user"),
        email=email or f"{_unique_str('user')}@example.com",
        password_hash="hashed",
        role=role,
        status=models.UserStatus.ACTIVE,
        created_at=_today(),
        last_login=None,
        creator=creator,
        creator_uuid=creator.uuid if creator else None,
    )


def build_project_model(
    *,
    creator: models.User,
    name: str | None = None,
    uuid: UUID | None = None,
) -> models.Project:
    return models.Project(
        uuid=uuid or uuid4(),
        name=name or _unique_str("project"),
        description="desc",
        creator=creator,
        creator_uuid=creator.uuid,
        start_date=None,
        end_date=None,
        status=models.ProjectStatus.ACTIVE,
        created_at=_today(),
    )


def build_membership_model(
    *,
    user: models.User,
    project: models.Project,
    assigned_by: models.User,
    uuid: UUID | None = None,
) -> models.MemberShip:
    return models.MemberShip(
        uuid=uuid or uuid4(),
        user=user,
        user_uuid=user.uuid,
        project=project,
        project_uuid=project.uuid,
        assigned_by_uuid=assigned_by.uuid,
        assigned_by_user=assigned_by,
        joined_at=_today(),
    )


def build_stage_model(
    *,
    creator: models.User,
    project: models.Project,
    parent: models.Stage | None = None,
    name: str | None = None,
    main_path: bool = True,
    uuid: UUID | None = None,
) -> models.Stage:
    return models.Stage(
        uuid=uuid or uuid4(),
        name=name or _unique_str("stage"),
        description="desc",
        creator=creator,
        creator_uuid=creator.uuid,
        project=project,
        project_uuid=project.uuid,
        parent=parent,
        parent_uuid=parent.uuid if parent else None,
        created_at=_today(),
        main_path=main_path,
        status=models.StageStatus.ACTIVE,
    )


def build_task_model(
    *,
    creator: models.User,
    substage: models.Stage,
    name: str | None = None,
    uuid: UUID | None = None,
) -> models.Task:
    return models.Task(
        uuid=uuid or uuid4(),
        name=name or _unique_str("task"),
        description="desc",
        creator=creator,
        creator_uuid=creator.uuid,
        substage=substage,
        substage_uuid=substage.uuid,
        created_at=_today(),
        status=models.TaskStatus.PENDING,
        completion_date=None,
        working_days=[_today()],
    )


def build_daily_log_model(
    *,
    creator: models.User,
    project: models.Project,
    substage: models.Stage | None = None,
    uuid: UUID | None = None,
) -> models.DailyLog:
    return models.DailyLog(
        uuid=uuid or uuid4(),
        creator=creator,
        creator_uuid=creator.uuid,
        project=project,
        project_uuid=project.uuid,
        substage=substage,
        substage_uuid=substage.uuid if substage else None,
        created_at=_today(),
        updated_at=None,
        draft=False,
        hours_spent=1.5,
        description="work",
    )


def build_subscription_model(
    *,
    project: models.Project,
    uuid: UUID | None = None,
) -> models.Subscription:
    return models.Subscription(
        uuid=uuid or uuid4(),
        project=project,
        project_uuid=project.uuid,
        created_at=_today(),
        auto_renew=True,
        start_date=_today(),
        end_date=_today(30),
        status=models.SubscriptionStatus.UNACTIVE,
    )


def build_payment_model(
    *,
    subscription: models.Subscription,
    uuid: UUID | None = None,
) -> models.Payment:
    return models.Payment(
        uuid=uuid or uuid4(),
        subscription=subscription,
        subscription_uuid=subscription.uuid,
        amount=100.0,
        currency=models.CurrencyEnum.RUB,
        status=models.PaymentStatus.PENDING,
        payment_method=models.PaymentMethod.CREDIT_CARD,
        payment_date=None,
        created_at=_today(),
    )


def build_file_model(
    *,
    daily_log: models.DailyLog,
    name: str | None = None,
    uri: str | None = None,
    uuid: UUID | None = None,
) -> models.DailyLogFile:
    return models.DailyLogFile(
        uuid=uuid or uuid4(),
        name=name or _unique_str("file"),
        uri=uri or f"s3://bucket/{_unique_str('file')}",
        uploaded_at=_today(),
        daily_log=daily_log,
        daily_log_uuid=daily_log.uuid,
    )


async def persist(session: AsyncSession, model: Any) -> Any:
    session.add(model)
    await session.flush()
    return model
