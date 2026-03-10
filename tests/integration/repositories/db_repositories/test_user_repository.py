from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from htimer.infrastructure.repositories import exceptions as repo_exceptions, interfaces as repository_interfaces
from htimer.domain import entities
from htimer.infrastructure.db import models
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_user_success(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)

    result = await user_repository.create(user)

    assert isinstance(result, entities.User)
    assert result.email == user.email


@pytest.mark.asyncio
async def test_create_user_email_exists(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)

    await user_repository.create(user)
    duplicate = factories.make_user_entity(role=entities.UserRole.ADMIN, email=user.email)
    result = await user_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.EmailAlreadyExistsError)


@pytest.mark.asyncio
async def test_update_user_success(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    created = await user_repository.create(user)
    assert isinstance(created, entities.User)

    result = await user_repository.update(created.uuid, {"name": "Updated"})

    assert isinstance(result, entities.User)
    assert result.name == "Updated"


@pytest.mark.asyncio
async def test_update_user_not_found(user_repository: repository_interfaces.DBUserRepository):
    result = await user_repository.update(uuid4(), {"name": "Updated"})

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_update_user_email_exists(user_repository: repository_interfaces.DBUserRepository):
    user1 = factories.make_user_entity(role=entities.UserRole.ADMIN)
    user2 = factories.make_user_entity(role=entities.UserRole.ADMIN)

    created1 = await user_repository.create(user1)
    created2 = await user_repository.create(user2)
    assert isinstance(created1, entities.User)
    assert isinstance(created2, entities.User)

    result = await user_repository.update(created2.uuid, {"email": created1.email})

    assert isinstance(result, repo_exceptions.EmailAlreadyExistsError)


@pytest.mark.asyncio
async def test_get_by_email_success(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    created = await user_repository.create(user)
    assert isinstance(created, entities.User)

    result = await user_repository.get_by_email(created.email)

    assert isinstance(result, entities.User)
    assert result.uuid == created.uuid


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repository: repository_interfaces.DBUserRepository):
    result = await user_repository.get_by_email("missing@example.com")

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    created = await user_repository.create(user)
    assert isinstance(created, entities.User)

    result = await user_repository.get_by_uuid(created.uuid)

    assert isinstance(result, entities.User)
    assert result.email == created.email


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(user_repository: repository_interfaces.DBUserRepository):
    result = await user_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success(user_repository: repository_interfaces.DBUserRepository):
    user1 = factories.make_user_entity(role=entities.UserRole.ADMIN)
    user2 = factories.make_user_entity(role=entities.UserRole.ADMIN)

    created1 = await user_repository.create(user1)
    created2 = await user_repository.create(user2)
    assert isinstance(created1, entities.User)
    assert isinstance(created2, entities.User)

    result = await user_repository.get_list([created1.uuid, created2.uuid])

    assert isinstance(result, list)
    assert {user.uuid for user in result} == {created1.uuid, created2.uuid}


@pytest.mark.asyncio
async def test_get_list_missing_user(user_repository: repository_interfaces.DBUserRepository):
    user = factories.make_user_entity(role=entities.UserRole.ADMIN)
    created = await user_repository.create(user)
    assert isinstance(created, entities.User)

    result = await user_repository.get_list([created.uuid, uuid4()])

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_get_projects_none_user(user_repository: repository_interfaces.DBUserRepository):
    result = await user_repository.get_projects(None)

    assert result == []


@pytest.mark.asyncio
async def test_get_projects_user_not_found(user_repository: repository_interfaces.DBUserRepository):
    result = await user_repository.get_projects(uuid4())

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_get_projects_owned_and_member(
    db_session: AsyncSession, user_repository: repository_interfaces.DBUserRepository
):
    owner_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.ADMIN)
    )
    member_model = await factories.persist(
        db_session, factories.build_user_model(role=models.UserRole.USER, creator=owner_model)
    )

    project_owned = await factories.persist(
        db_session, factories.build_project_model(creator=owner_model)
    )
    project_member = await factories.persist(
        db_session, factories.build_project_model(creator=owner_model)
    )

    membership = factories.build_membership_model(
        user=member_model, project=project_member, assigned_by=owner_model
    )
    await factories.persist(db_session, membership)

    result = await user_repository.get_projects(member_model.uuid)

    assert isinstance(result, list)
    project_uuids = {project.uuid for project in result}
    assert project_owned.uuid not in project_uuids
    assert project_member.uuid in project_uuids
