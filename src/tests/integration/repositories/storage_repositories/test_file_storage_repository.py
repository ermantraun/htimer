from datetime import date
from typing import cast
from uuid import uuid4
from unittest.mock import Mock

import pytest
import minio
from minio.error import S3Error
from urllib3.response import BaseHTTPResponse

from config import Config
from domain import entities
from infrastructure.file_storage import repositories as storage_repositories
from infrastructure.repositories import exceptions as repo_exceptions
from tests.integration import factories


def _build_file_entity() -> entities.DailyLogFile:
    owner = factories.make_user_entity(role=entities.UserRole.ADMIN)
    project = factories.make_project_entity(creator=owner)
    daily_log = factories.make_daily_log_entity(creator=owner, project=project)
    return entities.DailyLogFile(
        uuid=uuid4(),
        filename="report.pdf",
        uri="s3://bucket/report.pdf",
        daily_log=daily_log,
        uploaded_at=date.today(),
    )


def _s3_error(code: str, message: str) -> S3Error:
    response = Mock(spec=BaseHTTPResponse)
    return S3Error(
        code=code,
        message=message,
        resource="resource",
        request_id="request_id",
        host_id="host_id",
        response=response,
    )


@pytest.mark.asyncio
async def test_get_upload_link_success():
    config = Config()
    file = _build_file_entity()

    class _Client:
        def presigned_put_object(self, bucket_name: str, object_name: str, expires: object) -> str:
            return f"https://storage/{bucket_name}/{object_name}?upload=1"

    repository = storage_repositories.FileRepository(cast(minio.Minio, _Client()), config)

    result = await repository.get_upload_link(file)

    assert isinstance(result, str)
    assert str(file.uuid) in result


@pytest.mark.asyncio
async def test_get_unload_link_not_found():
    config = Config()
    file = _build_file_entity()

    class _Client:
        def presigned_get_object(self, bucket_name: str, object_name: str, expires: object) -> str:
            raise _s3_error("NoSuchKey", "missing")

    repository = storage_repositories.FileRepository(cast(minio.Minio, _Client()), config)

    result = await repository.get_unload_link(file)

    assert isinstance(result, repo_exceptions.FileNotFoundError)


@pytest.mark.asyncio
async def test_get_unload_link_list_success():
    config = Config()
    file1 = _build_file_entity()
    file2 = _build_file_entity()

    class _Client:
        def presigned_get_object(self, bucket_name: str, object_name: str, expires: object) -> str:
            return f"https://storage/{bucket_name}/{object_name}?download=1"

    repository = storage_repositories.FileRepository(cast(minio.Minio, _Client()), config)

    result = await repository.get_unload_link_list([file1, file2])

    assert isinstance(result, list)
    assert len(result) == 2
    assert {item[0].uuid for item in result} == {file1.uuid, file2.uuid}


@pytest.mark.asyncio
async def test_get_remove_link_not_found():
    config = Config()
    file = _build_file_entity()

    class _Client:
        def remove_object(self, bucket_name: str, object_name: str) -> None:
            raise _s3_error("NoSuchKey", "missing")

    repository = storage_repositories.FileRepository(cast(minio.Minio, _Client()), config)

    result = await repository.get_remove_link(file)

    assert isinstance(result, repo_exceptions.FileNotFoundError)
