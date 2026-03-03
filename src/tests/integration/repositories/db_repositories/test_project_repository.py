from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.repositories import exceptions as repo_exceptions, interfaces as repository_interfaces
from domain import entities
from infrastructure.db import models
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_project_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    created_user = await user_repository.create(user)
    assert isinstance(created_user, entities.User)

    project = factories.make_project_entity(creator=created_user)
    result = await project_repository.create(project)

    assert isinstance(result, entities.Project)
    assert result.name == project.name


@pytest.mark.asyncio
async def test_create_project_user_not_found(
    project_repository: repository_interfaces.DBProjectRepository,
):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    project = factories.make_project_entity(creator=user)

    result = await project_repository.create(project)

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_create_project_duplicate_name(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(factories.make_user_entity(role=entities.UserRole.ADMIN))
    assert isinstance(creator, entities.User)
    project = factories.make_project_entity(creator=creator, name="Same")
    await project_repository.create(project)

    duplicate = factories.make_project_entity(creator=creator, name="Same")
    result = await project_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.UserAlreadyHasProjectError)


@pytest.mark.asyncio
async def test_update_project_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(factories.make_user_entity(role=entities.UserRole.ADMIN))
    assert isinstance(creator, entities.User)

    project = await project_repository.create(factories.make_project_entity(creator=creator))
    assert isinstance(project, entities.Project)

    result = await project_repository.update(project.uuid, {"name": "Updated"})

    assert isinstance(result, entities.Project)
    assert result.name == "Updated"


@pytest.mark.asyncio
async def test_update_project_not_found(
    project_repository: repository_interfaces.DBProjectRepository,
):
    result = await project_repository.update(uuid4(), {"name": "Updated"})

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_update_project_duplicate_name(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(factories.make_user_entity(role=entities.UserRole.ADMIN))
    assert isinstance(creator, entities.User)

    project1 = await project_repository.create(factories.make_project_entity(creator=creator, name="A"))
    project2 = await project_repository.create(factories.make_project_entity(creator=creator, name="B"))
    assert isinstance(project1, entities.Project)
    assert isinstance(project2, entities.Project)

    result = await project_repository.update(project2.uuid, {"name": project1.name})

    assert isinstance(result, repo_exceptions.UserAlreadyHasProjectError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(creator, entities.User)
    project = await project_repository.create(factories.make_project_entity(creator=creator))
    assert isinstance(project, entities.Project)

    result = await project_repository.get_by_uuid(project.uuid)

    assert isinstance(result, entities.Project)
    assert result.uuid == project.uuid


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(
    project_repository: repository_interfaces.DBProjectRepository,
):
    result = await project_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_get_by_name_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(creator, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=creator, name="One")
    )
    assert isinstance(project, entities.Project)

    result = await project_repository.get_by_name(creator.uuid, "One")

    assert isinstance(result, entities.Project)
    assert result.uuid == project.uuid


@pytest.mark.asyncio
async def test_get_by_name_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    creator = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(creator, entities.User)

    result = await project_repository.get_by_name(creator.uuid, "Missing")

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_add_members_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    member = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.EXECUTOR, creator=owner)
    )
    assert isinstance(member, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    membership = factories.make_membership_entity(
        user=member, project=project, assigned_by=owner
    )

    result = await project_repository.add_members([membership])

    assert isinstance(result, list)
    assert result[0].user.uuid == member.uuid


@pytest.mark.asyncio
async def test_add_members_project_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    member = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.EXECUTOR, creator=owner)
    )
    assert isinstance(member, entities.User)

    missing_project = factories.make_project_entity(creator=owner)
    membership = factories.make_membership_entity(
        user=member, project=missing_project, assigned_by=owner
    )

    result = await project_repository.add_members([membership])

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_add_members_user_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    missing_user = factories.make_user_entity(role=entities.UserRole.EXECUTOR, creator=owner)
    membership = factories.make_membership_entity(
        user=missing_user, project=project, assigned_by=owner
    )

    result = await project_repository.add_members([membership])

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_add_members_user_already_member(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    member = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.EXECUTOR, creator=owner)
    )
    assert isinstance(member, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    membership = factories.make_membership_entity(
        user=member, project=project, assigned_by=owner
    )
    await project_repository.add_members([membership])

    duplicate = factories.make_membership_entity(
        user=member, project=project, assigned_by=owner
    )
    result = await project_repository.add_members([duplicate])

    assert isinstance(result, repo_exceptions.UserAlreadyProjectMemberError)


@pytest.mark.asyncio
async def test_remove_members_success(
    db_session: AsyncSession,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.ADMIN)
    )
    member_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.USER, creator=owner_model)
    )
    project_model = await factories.persist(
        db_session, factories.build_project_model(creator=owner_model)
    )
    membership = factories.build_membership_model(
        user=member_model, project=project_model, assigned_by=owner_model
    )
    await factories.persist(db_session, membership)

    result = await project_repository.remove_members(project_model.uuid, [member_model.uuid])

    assert result is None


@pytest.mark.asyncio
async def test_remove_members_not_found(
    db_session: AsyncSession,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.ADMIN)
    )
    project_model = await factories.persist(
        db_session, factories.build_project_model(creator=owner_model)
    )

    result = await project_repository.remove_members(project_model.uuid, [uuid4()])

    assert isinstance(result, repo_exceptions.MemberNotFound)


@pytest.mark.asyncio
async def test_get_members_success(
    db_session: AsyncSession,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.ADMIN)
    )
    member_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.USER, creator=owner_model)
    )
    project_model = await factories.persist(
        db_session, factories.build_project_model(creator=owner_model)
    )
    membership = factories.build_membership_model(
        user=member_model, project=project_model, assigned_by=owner_model
    )
    await factories.persist(db_session, membership)

    result = await project_repository.get_members([project_model.uuid], is_active=False)

    assert isinstance(result, list)
    assert result[0].uuid == member_model.uuid


@pytest.mark.asyncio
async def test_get_members_project_not_found(
    project_repository: repository_interfaces.DBProjectRepository,
):
    result = await project_repository.get_members([uuid4()])

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_get_current_subscription_success(
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

    created_subscription = await subscription_repository.create(
        factories.make_subscription_entity(project=project)
    )
    assert isinstance(created_subscription, entities.Subscription)

    result = await project_repository.get_current_subscription(project.uuid)

    assert isinstance(result, entities.Subscription)
    assert result.uuid == created_subscription.uuid


@pytest.mark.asyncio
async def test_get_current_subscription_project_not_found(
    project_repository: repository_interfaces.DBProjectRepository,
):
    result = await project_repository.get_current_subscription(uuid4())

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_get_current_subscription_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    result = await project_repository.get_current_subscription(project.uuid)

    assert isinstance(result, repo_exceptions.SubscriptionNotFoundError)
