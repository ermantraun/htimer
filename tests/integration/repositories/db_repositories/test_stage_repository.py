from uuid import uuid4

import pytest

from htimer.domain import entities
from htimer.infrastructure.repositories import exceptions as repo_exceptions
from htimer.infrastructure.repositories import interfaces as repository_interfaces
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_stage_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    stage = factories.make_stage_entity(
        creator=owner, project=project, main_path=True, parent=None
    )

    result = await stage_repository.create(stage)

    assert isinstance(result, entities.Stage)
    assert result.name == stage.name


@pytest.mark.asyncio
async def test_create_stage_project_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    user = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(user, entities.User)
    missing_project = factories.make_project_entity(creator=user)
    stage = factories.make_stage_entity(
        creator=user, project=missing_project, main_path=True, parent=None
    )

    result = await stage_repository.create(stage)

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_create_stage_user_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = factories.make_user_entity(role=entities.UserRole.ADMIN)
    project_owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(project_owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=project_owner)
    )
    assert isinstance(project, entities.Project)

    stage = factories.make_stage_entity(
        creator=owner, project=project, main_path=True, parent=None
    )

    result = await stage_repository.create(stage)

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_create_stage_duplicate_name_in_parent(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    parent = await stage_repository.create(
        factories.make_stage_entity(creator=owner, project=project, main_path=True)
    )
    assert isinstance(parent, entities.Stage)

    stage1 = factories.make_stage_entity(
        creator=owner, project=project, parent=parent, name="Sub", main_path=False
    )
    await stage_repository.create(stage1)

    stage2 = factories.make_stage_entity(
        creator=owner, project=project, parent=parent, name="Sub", main_path=False
    )
    result = await stage_repository.create(stage2)

    assert isinstance(result, repo_exceptions.StageAlreadyExistsError)


@pytest.mark.asyncio
async def test_update_stage_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = await stage_repository.create(
        factories.make_stage_entity(creator=owner, project=project, main_path=True)
    )
    assert isinstance(stage, entities.Stage)

    result = await stage_repository.update(stage.uuid, {"name": "Updated"})

    assert isinstance(result, entities.Stage)
    assert result.name == "Updated"


@pytest.mark.asyncio
async def test_update_stage_not_found(
    stage_repository: repository_interfaces.DBStageRepository,
):
    result = await stage_repository.update(uuid4(), {"name": "Updated"})

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_delete_stage_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = await stage_repository.create(
        factories.make_stage_entity(creator=owner, project=project, main_path=True)
    )
    assert isinstance(stage, entities.Stage)

    result = await stage_repository.delete(stage.uuid)

    assert result is None


@pytest.mark.asyncio
async def test_delete_stage_not_found(
    stage_repository: repository_interfaces.DBStageRepository,
):
    result = await stage_repository.delete(uuid4())

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_get_by_name_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, name="Stage", main_path=True
        )
    )
    assert isinstance(stage, entities.Stage)

    result = await stage_repository.get_by_name(project.uuid, "Stage")

    assert isinstance(result, entities.Stage)
    assert result.uuid == stage.uuid


@pytest.mark.asyncio
async def test_get_by_name_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    result = await stage_repository.get_by_name(project.uuid, "Missing")

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = await stage_repository.create(
        factories.make_stage_entity(creator=owner, project=project, main_path=True)
    )
    assert isinstance(stage, entities.Stage)

    result = await stage_repository.get_by_uuid(stage.uuid)

    assert isinstance(result, entities.Stage)
    assert result.uuid == stage.uuid


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(
    stage_repository: repository_interfaces.DBStageRepository,
):
    result = await stage_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = await stage_repository.create(
        factories.make_stage_entity(creator=owner, project=project, main_path=True)
    )
    assert isinstance(stage, entities.Stage)

    result = await stage_repository.get_list(project.uuid)

    assert isinstance(result, list)
    assert result[0].uuid == stage.uuid


@pytest.mark.asyncio
async def test_get_list_project_not_found(
    stage_repository: repository_interfaces.DBStageRepository,
):
    result = await stage_repository.get_list(uuid4())

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)
