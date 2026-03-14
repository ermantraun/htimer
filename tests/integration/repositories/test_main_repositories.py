from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities
from htimer.infrastructure.repositories import exceptions as repo_exceptions
from tests.integration import factories


def _build_user() -> entities.User:
    return factories.make_user_entity(role=entities.UserRole.ADMIN)


def _build_project() -> entities.Project:
    owner = _build_user()
    return factories.make_project_entity(creator=owner)


def _build_daily_log() -> entities.DailyLog:
    owner = _build_user()
    project = factories.make_project_entity(creator=owner)
    return factories.make_daily_log_entity(creator=owner, project=project)


def _build_subscription() -> entities.Subscription:
    project = _build_project()
    return factories.make_subscription_entity(project=project)


def _build_payment() -> entities.Payment:
    subscription = _build_subscription()
    return factories.make_payment_entity(subscription=subscription)


@pytest.mark.asyncio
async def test_user_repository_maps_exception(
    main_user_repository: common_interfaces.UserRepository,
):
    repository = cast(Any, main_user_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_uuid.return_value = repo_exceptions.UserNotFoundError(
        "missing"
    )

    result = await repository.get_by_uuid(uuid4())

    assert isinstance(result, common_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_project_repository_passes_success(
    main_project_repository: common_interfaces.ProjectRepository,
):
    project = _build_project()
    repository = cast(Any, main_project_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_uuid.return_value = project

    result = await repository.get_by_uuid(project.uuid)

    assert isinstance(result, entities.Project)
    assert result.uuid == project.uuid


@pytest.mark.asyncio
async def test_stage_repository_maps_exception(
    main_stage_repository: common_interfaces.StageRepository,
):
    repository = cast(Any, main_stage_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_name.return_value = repo_exceptions.StageNotFoundError(
        "missing"
    )

    result = await repository.get_by_name(uuid4(), "missing")

    assert isinstance(result, common_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_daily_log_repository_passes_success(
    main_daily_log_repository: common_interfaces.DailyLogRepository,
):
    daily_log = _build_daily_log()
    repository = cast(Any, main_daily_log_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_uuid.return_value = daily_log

    result = await repository.get_by_uuid(daily_log.uuid)

    assert isinstance(result, entities.DailyLog)
    assert result.uuid == daily_log.uuid


@pytest.mark.asyncio
async def test_task_repository_maps_exception(
    main_task_repository: common_interfaces.TaskRepository,
):
    repository = cast(Any, main_task_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_uuid.return_value = repo_exceptions.TaskNotFoundError(
        "missing"
    )

    result = await repository.get_by_uuid(uuid4())

    assert isinstance(result, common_exceptions.TaskNotFoundError)


@pytest.mark.asyncio
async def test_payment_repository_passes_success(
    main_payment_repository: common_interfaces.PaymentRepository,
):
    payment = _build_payment()
    repository = cast(Any, main_payment_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_uuid.return_value = payment

    result = await repository.get_by_uuid(payment.uuid)

    assert isinstance(result, entities.Payment)
    assert result.uuid == payment.uuid


@pytest.mark.asyncio
async def test_subscription_repository_maps_exception(
    main_subscription_repository: common_interfaces.SubscriptionRepository,
):
    repository = cast(Any, main_subscription_repository)
    repository._db_rep = AsyncMock()
    repository._db_rep.get_by_project_uuid.return_value = (
        repo_exceptions.SubscriptionNotFoundError("missing")
    )

    result = await repository.get_by_project_uuid(uuid4())

    assert isinstance(result, common_exceptions.SubscriptionNotFoundError)
