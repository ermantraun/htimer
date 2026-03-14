from uuid import uuid4

import pytest

from htimer.domain import entities
from htimer.infrastructure.db import models
from htimer.infrastructure.repositories import exceptions as repo_exceptions
from htimer.infrastructure.repositories import interfaces as repository_interfaces
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_payment_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
    payment_repository: repository_interfaces.DBPaymentRepository,
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
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    payment_repository: repository_interfaces.DBPaymentRepository,
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

    assert isinstance(result, repo_exceptions.SubscriptionNotFoundError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
    payment_repository: repository_interfaces.DBPaymentRepository,
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
    payment_repository: repository_interfaces.DBPaymentRepository,
):
    result = await payment_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.PaymentNotFoundError)


@pytest.mark.asyncio
async def test_update_payment_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
    payment_repository: repository_interfaces.DBPaymentRepository,
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
    payment_repository: repository_interfaces.DBPaymentRepository,
):
    result = await payment_repository.update(
        uuid4(), {"status": models.PaymentStatus.COMPLETED}
    )

    assert isinstance(result, repo_exceptions.PaymentNotFoundError)
