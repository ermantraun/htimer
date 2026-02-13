from uuid import uuid4

import pytest

from application import common_exceptions, common_interfaces
from domain import entities
from infrastructure.db import models
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_payment_success(
    user_repository: common_interfaces.UserRepository,
    project_repository: common_interfaces.ProjectRepository,
    subscription_repository: common_interfaces.SubscriptionRepository,
    payment_repository: common_interfaces.PaymentRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    subscription = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(subscription, entities.Subscription)

    payment = factories.make_payment_entity(subscription=subscription)
    result = await payment_repository.create(payment)

    assert isinstance(result, entities.Payment)
    assert result.uuid == payment.uuid


@pytest.mark.asyncio
async def test_create_payment_subscription_not_found(
    user_repository: common_interfaces.UserRepository,
    project_repository: common_interfaces.ProjectRepository,
    payment_repository: common_interfaces.PaymentRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    subscription = factories.make_subscription_entity(project=project)

    payment = factories.make_payment_entity(subscription=subscription)
    result = await payment_repository.create(payment)

    assert isinstance(result, common_exceptions.SubscriptionNotFoundError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: common_interfaces.UserRepository,
    project_repository: common_interfaces.ProjectRepository,
    subscription_repository: common_interfaces.SubscriptionRepository,
    payment_repository: common_interfaces.PaymentRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    subscription = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(subscription, entities.Subscription)

    payment = await payment_repository.create(
        factories.make_payment_entity(subscription=subscription)
    )
    assert isinstance(payment, entities.Payment)

    result = await payment_repository.get_by_uuid(payment.uuid)

    assert isinstance(result, entities.Payment)
    assert result.uuid == payment.uuid


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(
    payment_repository: common_interfaces.PaymentRepository,
):
    result = await payment_repository.get_by_uuid(uuid4())

    assert isinstance(result, common_exceptions.PaymentNotFoundError)


@pytest.mark.asyncio
async def test_update_payment_success(
    user_repository: common_interfaces.UserRepository,
    project_repository: common_interfaces.ProjectRepository,
    subscription_repository: common_interfaces.SubscriptionRepository,
    payment_repository: common_interfaces.PaymentRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    subscription = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(subscription, entities.Subscription)

    payment = await payment_repository.create(
        factories.make_payment_entity(subscription=subscription)
    )
    assert isinstance(payment, entities.Payment)

    result = await payment_repository.update(
        payment.uuid, {"status": models.PaymentStatus.COMPLETED}
    )

    assert isinstance(result, entities.Payment)
    assert result.status == entities.PaymentStatus.COMPLETED


@pytest.mark.asyncio
async def test_update_payment_not_found(
    payment_repository: common_interfaces.PaymentRepository,
):
    result = await payment_repository.update(uuid4(), {"status": models.PaymentStatus.COMPLETED})

    assert isinstance(result, common_exceptions.PaymentNotFoundError)
