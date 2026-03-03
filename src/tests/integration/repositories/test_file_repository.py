from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from application import common_exceptions, common_interfaces
from domain import entities
from infrastructure.db import repositories as db_repositories
from infrastructure.repositories import repositories as common_repositories
from infrastructure.repositories import exceptions as repo_exceptions
from tests.integration import factories


def _build_file_entity() -> entities.DailyLogFile:
    owner = factories.make_user_entity(role=entities.UserRole.ADMIN)
    project = factories.make_project_entity(creator=owner)
    daily_log = factories.make_daily_log_entity(creator=owner, project=project)
    return factories.make_file_entity(daily_log=daily_log)


@pytest.mark.asyncio
async def test_create_success_returns_action_link():
    session = AsyncMock()
    file = _build_file_entity()

    db_rep = AsyncMock()
    db_rep.create.return_value = file

    storage_rep = AsyncMock()
    storage_rep.get_upload_link.return_value = "https://storage/upload"

    repository = common_repositories.FileRepository(session, db_rep, storage_rep)

    result = await repository.create(file)

    assert isinstance(result, tuple)
    entity, link = result
    assert entity.uuid == file.uuid
    assert isinstance(link, common_interfaces.ActionLink)
    assert link.link == "https://storage/upload"


@pytest.mark.asyncio
async def test_create_rollbacks_on_storage_error():
    session = AsyncMock()
    file = _build_file_entity()

    db_rep = AsyncMock()
    db_rep.create.return_value = file

    storage_rep = AsyncMock()
    storage_rep.get_upload_link.return_value = repo_exceptions.FileRepositoryError("failed")

    repository = common_repositories.FileRepository(session, db_rep, storage_rep)

    result = await repository.create(file)

    assert isinstance(result, common_exceptions.FileRepositoryError)
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_maps_not_found_error():
    session = AsyncMock()

    db_rep = AsyncMock()
    db_rep.get.return_value = repo_exceptions.FileNotFoundError("missing")

    storage_rep = AsyncMock()

    repository = common_repositories.FileRepository(session, db_rep, storage_rep)

    result = await repository.get(uuid4())

    assert isinstance(result, common_exceptions.FileNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success_maps_links():
    session = AsyncMock()
    file1 = _build_file_entity()
    file2 = _build_file_entity()

    db_rep = AsyncMock()
    db_rep.get_list.return_value = [file1, file2]

    storage_rep = AsyncMock()
    storage_rep.get_unload_link_list.return_value = [
        (file1, "https://storage/file1"),
        (file2, "https://storage/file2"),
    ]

    repository = common_repositories.FileRepository(session, db_rep, storage_rep)

    result = await repository.get_list(file1.daily_log.uuid)

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0][1], common_interfaces.ActionLink)
    assert result[0][1].link == "https://storage/file1"


@pytest.mark.asyncio
async def test_remove_storage_error_rollbacks():
    session = AsyncMock()
    file = _build_file_entity()

    db_rep = AsyncMock()
    db_rep.remove.return_value = file

    storage_rep = AsyncMock()
    storage_rep.get_remove_link.return_value = repo_exceptions.FileRepositoryError("failed")

    repository = common_repositories.FileRepository(session, db_rep, storage_rep)

    result = await repository.remove(file.uuid)

    assert isinstance(result, common_exceptions.FileRepositoryError)
    session.rollback.assert_awaited_once()


def test_map_file_entity_to_model():
    file = _build_file_entity()

    model = db_repositories.FileRepository.map_entity_to_file(file)

    assert model.uuid == file.uuid
    assert model.name == file.filename
    assert model.uri == file.uri
    assert model.daily_log_uuid == file.daily_log.uuid


def test_map_file_model_to_entity():
    owner = factories.build_user_model()
    project = factories.build_project_model(creator=owner)
    daily_log = factories.build_daily_log_model(creator=owner, project=project)
    file_model = factories.build_file_model(daily_log=daily_log)

    entity = db_repositories.FileRepository.map_file_to_entity(file_model)

    assert entity.uuid == file_model.uuid
    assert entity.filename == file_model.name
    assert entity.daily_log.uuid == daily_log.uuid
