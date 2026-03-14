from uuid import uuid4

import pytest

from htimer.domain import entities
from htimer.infrastructure.repositories import exceptions as repo_exceptions
from htimer.infrastructure.repositories import interfaces as repository_interfaces
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_task_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = factories.make_task_entity(creator=owner, substage=substage)
    result = await task_repository.create(task)

    assert isinstance(result, entities.Task)
    assert result.uuid == task.uuid


@pytest.mark.asyncio
async def test_create_task_stage_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    task_repository: repository_interfaces.DBTaskRepository,
):
    owner = await user_repository.create(
        factories.make_user_entity(role=entities.UserRole.ADMIN)
    )
    assert isinstance(owner, entities.User)
    project = await project_repository.create(
        factories.make_project_entity(creator=owner)
    )
    assert isinstance(project, entities.Project)
    stage = factories.make_stage_entity(creator=owner, project=project, main_path=True)

    task = factories.make_task_entity(creator=owner, substage=stage)
    result = await task_repository.create(task)

    assert isinstance(result, repo_exceptions.StageNotFoundError)


@pytest.mark.asyncio
async def test_create_task_user_not_found(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    missing_user = factories.make_user_entity(
        role=entities.UserRole.EXECUTOR, creator=owner
    )
    task = factories.make_task_entity(creator=missing_user, substage=substage)
    result = await task_repository.create(task)

    assert isinstance(result, repo_exceptions.UserNotFoundError)


@pytest.mark.asyncio
async def test_create_task_already_exists(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = factories.make_task_entity(creator=owner, substage=substage, name="Task")
    await task_repository.create(task)

    duplicate = factories.make_task_entity(
        creator=owner, substage=substage, name="Task"
    )
    result = await task_repository.create(duplicate)

    assert isinstance(result, repo_exceptions.TaskAlreadyExistsError)


@pytest.mark.asyncio
async def test_get_by_uuid_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage)
    )
    assert isinstance(task, entities.Task)

    result = await task_repository.get_by_uuid(task.uuid)

    assert isinstance(result, entities.Task)
    assert result.uuid == task.uuid


@pytest.mark.asyncio
async def test_get_by_uuid_not_found(
    task_repository: repository_interfaces.DBTaskRepository,
):
    result = await task_repository.get_by_uuid(uuid4())

    assert isinstance(result, repo_exceptions.TaskNotFoundError)


@pytest.mark.asyncio
async def test_update_task_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage)
    )
    assert isinstance(task, entities.Task)

    result = await task_repository.update(task.uuid, {"name": "Updated"})

    assert isinstance(result, entities.Task)
    assert result.name == "Updated"


@pytest.mark.asyncio
async def test_update_task_not_found(
    task_repository: repository_interfaces.DBTaskRepository,
):
    result = await task_repository.update(uuid4(), {"name": "Updated"})

    assert isinstance(result, repo_exceptions.TaskNotFoundError)


@pytest.mark.asyncio
async def test_update_task_already_exists(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task1 = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage, name="A")
    )
    task2 = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage, name="B")
    )
    assert isinstance(task1, entities.Task)
    assert isinstance(task2, entities.Task)

    result = await task_repository.update(task2.uuid, {"name": task1.name})

    assert isinstance(result, repo_exceptions.TaskAlreadyExistsError)


@pytest.mark.asyncio
async def test_delete_task_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage)
    )
    assert isinstance(task, entities.Task)

    result = await task_repository.delete(task.uuid)

    assert result is None


@pytest.mark.asyncio
async def test_delete_task_not_found(
    task_repository: repository_interfaces.DBTaskRepository,
):
    result = await task_repository.delete(uuid4())

    assert isinstance(result, repo_exceptions.TaskNotFoundError)


@pytest.mark.asyncio
async def test_get_list_success(
    user_repository: repository_interfaces.DBUserRepository,
    project_repository: repository_interfaces.DBProjectRepository,
    stage_repository: repository_interfaces.DBStageRepository,
    task_repository: repository_interfaces.DBTaskRepository,
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
    substage = await stage_repository.create(
        factories.make_stage_entity(
            creator=owner, project=project, parent=stage, main_path=False
        )
    )
    assert isinstance(substage, entities.Stage)

    task = await task_repository.create(
        factories.make_task_entity(creator=owner, substage=substage)
    )
    assert isinstance(task, entities.Task)

    result = await task_repository.get_list(substage.uuid)

    assert isinstance(result, list)
    assert result[0].uuid == task.uuid


@pytest.mark.asyncio
async def test_get_list_stage_not_found(
    task_repository: repository_interfaces.DBTaskRepository,
):
    result = await task_repository.get_list(uuid4())

    assert isinstance(result, repo_exceptions.StageNotFoundError)
