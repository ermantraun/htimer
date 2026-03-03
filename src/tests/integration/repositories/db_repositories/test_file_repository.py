from uuid import uuid4

import pytest

from domain import entities
from infrastructure.repositories import exceptions as repo_exceptions, interfaces as repository_interfaces
from tests.integration import factories


async def _prepare_daily_log(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
) -> entities.DailyLog:
    owner = await user_repository.create(factories.make_user_entity(role=entities.UserRole.ADMIN))
    assert isinstance(owner, entities.User)

    project = await project_repository.create(factories.make_project_entity(creator=owner))
    assert isinstance(project, entities.Project)

    daily_log = await daily_log_repository.create(
        factories.make_daily_log_entity(creator=owner, project=project)
    )
    assert isinstance(daily_log, entities.DailyLog)

    return daily_log


@pytest.mark.asyncio
async def test_create_file_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
    db_file_repository: repository_interfaces.DBFileRepository,
):
    daily_log = await _prepare_daily_log(user_repository, project_repository, daily_log_repository)
    file = factories.make_file_entity(daily_log=daily_log)

    result = await db_file_repository.create(file)

    assert isinstance(result, entities.DailyLogFile)
    assert result.uuid == file.uuid
    assert result.filename == file.filename


@pytest.mark.asyncio
async def test_create_file_duplicate_name(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
    db_file_repository: repository_interfaces.DBFileRepository,
):
    daily_log = await _prepare_daily_log(user_repository, project_repository, daily_log_repository)
    first_file = factories.make_file_entity(daily_log=daily_log, filename="dup-name")
    await db_file_repository.create(first_file)

    duplicate = factories.make_file_entity(daily_log=daily_log, filename="dup-name")
    result = await db_file_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.FileAlreadyExistsError)


@pytest.mark.asyncio
async def test_get_file_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
    db_file_repository: repository_interfaces.DBFileRepository,
):
    daily_log = await _prepare_daily_log(user_repository, project_repository, daily_log_repository)
    file = factories.make_file_entity(daily_log=daily_log)
    created = await db_file_repository.create(file)
    assert isinstance(created, entities.DailyLogFile)

    result = await db_file_repository.get(created.uuid)

    assert isinstance(result, entities.DailyLogFile)
    assert result.uuid == created.uuid


@pytest.mark.asyncio
async def test_get_file_not_found(
    db_file_repository: repository_interfaces.DBFileRepository,
):
    result = await db_file_repository.get(uuid4())

    assert isinstance(result, repo_exceptions.FileNotFoundError)


@pytest.mark.asyncio
async def test_remove_file_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
    db_file_repository: repository_interfaces.DBFileRepository,
):
    daily_log = await _prepare_daily_log(user_repository, project_repository, daily_log_repository)
    file = factories.make_file_entity(daily_log=daily_log)
    created = await db_file_repository.create(file)
    assert isinstance(created, entities.DailyLogFile)

    removed = await db_file_repository.remove(created.uuid)

    assert isinstance(removed, entities.DailyLogFile)
    assert removed.uuid == created.uuid

    after_remove = await db_file_repository.get(created.uuid)
    assert isinstance(after_remove, repo_exceptions.FileNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    daily_log_repository: repository_interfaces.DBDailyLogRepository,
    db_file_repository: repository_interfaces.DBFileRepository,
):
    daily_log = await _prepare_daily_log(user_repository, project_repository, daily_log_repository)
    first = factories.make_file_entity(daily_log=daily_log)
    second = factories.make_file_entity(daily_log=daily_log)

    created_first = await db_file_repository.create(first)
    created_second = await db_file_repository.create(second)
    assert isinstance(created_first, entities.DailyLogFile)
    assert isinstance(created_second, entities.DailyLogFile)

    result = await db_file_repository.get_list(daily_log.uuid)

    assert isinstance(result, list)
    assert {item.uuid for item in result} == {created_first.uuid, created_second.uuid}


@pytest.mark.asyncio
async def test_get_list_not_found(
    db_file_repository: repository_interfaces.DBFileRepository,
):
    result = await db_file_repository.get_list(uuid4())

    assert isinstance(result, repo_exceptions.FileNotFoundError)
