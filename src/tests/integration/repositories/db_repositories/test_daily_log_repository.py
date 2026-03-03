from datetime import date
from uuid import uuid4

import pytest

from infrastructure.repositories import exceptions as repo_exceptions, interfaces as repository_interfaces
from domain import entities
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_daily_log_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    daily_log = factories.make_daily_log_entity(creator=owner, project=project)
    result = await daily_log_repository.create(daily_log)

    assert isinstance(result, entities.DailyLog)
    assert result.uuid == daily_log.uuid


@pytest.mark.asyncio
async def test_create_daily_log_project_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = factories.make_project_entity(creator=owner)
    daily_log = factories.make_daily_log_entity(creator=owner, project=project)

    result = await daily_log_repository.create(daily_log)

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)


@pytest.mark.asyncio
async def test_create_daily_log_user_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
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

    daily_log = factories.make_daily_log_entity(creator=owner, project=project)

    result = await daily_log_repository.create(daily_log)

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_create_daily_log_stage_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    missing_stage = factories.make_stage_entity(creator=owner, project=project, main_path=True)
    daily_log = factories.make_daily_log_entity(
        creator=owner, project=project, substage=missing_stage
    )

    result = await daily_log_repository.create(daily_log)

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_create_daily_log_already_exists(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    daily_log = factories.make_daily_log_entity(creator=owner, project=project)
    await daily_log_repository.create(daily_log)

    duplicate = factories.make_daily_log_entity(
        creator=owner, project=project, uuid=uuid4()
    )
    result = await daily_log_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.DailyLogAlreadyExistsError)


@pytest.mark.asyncio
async def test_update_daily_log_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    daily_log = await daily_log_repository.create(
        factories.make_daily_log_entity(creator=owner, project=project)
    )
    assert isinstance(daily_log, entities.DailyLog)

    result = await daily_log_repository.update(daily_log.uuid, {"description": "Updated"})

    assert isinstance(result, entities.DailyLog)
    assert result.description == "Updated"


@pytest.mark.asyncio
async def test_update_daily_log_not_found(
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    result = await daily_log_repository.update(uuid4(), {"description": "Updated"})

    assert isinstance(result, repo_exceptions.DailyLogNotFoundError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    daily_log = await daily_log_repository.create(
        factories.make_daily_log_entity(creator=owner, project=project)
    )
    assert isinstance(daily_log, entities.DailyLog)

    result = await daily_log_repository.get_by_uuid(daily_log.uuid)

    assert isinstance(result, entities.DailyLog)
    assert result.uuid == daily_log.uuid


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    result = await daily_log_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.DailyLogNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)

    first = await daily_log_repository.create(
        factories.make_daily_log_entity(creator=owner, project=project)
    )
    assert isinstance(first, entities.DailyLog)

    second_creator = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.EXECUTOR, creator=owner)
    )
    assert isinstance(second_creator, entities.User)

    second_entity = factories.make_daily_log_entity(creator=second_creator, project=project)
    second_entity.draft = True
    second = await daily_log_repository.create(second_entity)
    assert isinstance(second, entities.DailyLog)

    result_all = await daily_log_repository.get_list(project.uuid, date.today())
    assert isinstance(result_all, list)
    assert len(result_all) >= 2

    result_draft = await daily_log_repository.get_list(project.uuid, date.today(), draft=True)
    assert isinstance(result_draft, list)
    assert len(result_draft) == 1
    assert result_draft[0].uuid == second.uuid


@pytest.mark.asyncio
async def test_get_list_project_not_found(
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
):
    result = await daily_log_repository.get_list(uuid4(), date.today())

    assert isinstance(result, repo_exceptions.ProjectNotFoundError)
