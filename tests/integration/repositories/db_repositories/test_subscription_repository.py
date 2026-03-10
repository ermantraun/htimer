from uuid import uuid4

import pytest

from htimer.infrastructure.repositories import exceptions as repo_exceptions, interfaces as repository_interfaces
from htimer.domain import entities
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_subscription_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
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
    result = await subscription_repository.create(subscription)

    assert isinstance(result, entities.Subscription)
    assert result.uuid == subscription.uuid


@pytest.mark.asyncio
async def test_create_subscription_project_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = factories.make_project_entity(creator=owner)

    subscription = factories.make_subscription_entity(project=project)
    result = await subscription_repository.create(subscription)

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_create_subscription_already_exists(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )

    duplicate = factories.make_subscription_entity(project=project, uuid=uuid4())
    result = await subscription_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.SubscriptionAlreadyExistsError)


@pytest.mark.asyncio
async def test_get_by_project_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    created = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(created, entities.Subscription)

    result = await subscription_repository.get_by_project_uuid(project.uuid)

    assert isinstance(result, entities.Subscription)
    assert result.uuid == created.uuid


@pytest.mark.asyncio
async def test_get_by_project_uuid_not_found(
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    result = await subscription_repository.get_by_project_uuid(uuid4())

    assert isinstance(result, repo_exceptions.SubscriptionNotFoundError)


@pytest.mark.asyncio
async def test_update_subscription_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    created = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(created, entities.Subscription)

    result = await subscription_repository.update(created.uuid, {"auto_renew": False})

    assert isinstance(result, entities.Subscription)
    assert result.auto_renew is False


@pytest.mark.asyncio
async def test_update_subscription_not_found(
    subscription_repository: repository_interfaces.DBSubscriptionRepository,
):
    result = await subscription_repository.update(uuid4(), {"auto_renew": False})

    assert isinstance(result, repo_exceptions.SubscriptionNotFoundError)
