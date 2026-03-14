import asyncio
import io
from datetime import timedelta

import minio

from htimer.application import common_exceptions as exceptions
from htimer.application.common_interfaces import FileStorage
from htimer.config import Config


class Storage(FileStorage):
    def __init__(self, client: minio.Minio, config: Config):
        self.client = client
        self.bucket_name = config.minio.bucket_name

    async def save(
        self, file_name: str, content: bytes
    ) -> None | exceptions.FileStorageError:

        def _save():
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=io.BytesIO(content),
                length=len(content),
            )

        try:
            await asyncio.to_thread(_save)
        except minio.S3Error as e:
            # No specific code for already exists in MinIO for put_object; return generic storage error
            return exceptions.FileStorageError(f"Ошибка файлового хранилища: {e}")

    async def get_unload_link(
        self, file_name: str
    ) -> str | exceptions.FileNotFoundInStorageError | exceptions.FileStorageError:
        def _get_unload_link():
            return self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                expires=timedelta(minutes=15),
            )

        try:
            return await asyncio.to_thread(_get_unload_link)
        except minio.S3Error as e:
            if getattr(e, "code", None) == "NoSuchKey":
                return exceptions.FileNotFoundInStorageError(
                    f"Файл с именем {file_name} не найден в хранилище."
                )
            return exceptions.FileStorageError(f"Ошибка файлового хранилища: {e}")

    async def get_upload_link(
        self, file_name: str
    ) -> str | exceptions.FileStorageError:
        def _get_upload_link():
            return self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                expires=timedelta(minutes=15),
            )

        try:
            return await asyncio.to_thread(_get_upload_link)
        except minio.S3Error as e:
            return exceptions.FileStorageError(f"Ошибка файлового хранилища: {e}")

    async def get_unload_link_list(
        self, files: list[str]
    ) -> (
        list[tuple[str, str]]
        | exceptions.FileNotFoundInStorageError
        | exceptions.FileStorageError
    ):
        def _get_unload_link_list(file_name: str):
            link = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                expires=timedelta(minutes=15),
            )
            return (file_name, link)

        try:
            tasks = [
                asyncio.to_thread(_get_unload_link_list, file_name)
                for file_name in files
            ]
            return await asyncio.gather(*tasks)
        except minio.S3Error as e:
            if getattr(e, "code", None) == "NoSuchKey":
                return exceptions.FileNotFoundInStorageError(
                    "Один или несколько файлов не найдены в хранилище."
                )
            return exceptions.FileStorageError(f"Ошибка файлового хранилища: {e}")

    async def remove(
        self, file_name: str
    ) -> None | exceptions.FileNotFoundInStorageError | exceptions.FileStorageError:
        def _remove():
            self.client.remove_object(
                bucket_name=self.bucket_name, object_name=file_name
            )

        try:
            await asyncio.to_thread(_remove)
        except minio.S3Error as e:
            if getattr(e, "code", None) == "NoSuchKey":
                return exceptions.FileNotFoundInStorageError(
                    f"Файл с именем {file_name} не найден в хранилище."
                )
            return exceptions.FileStorageError(f"Ошибка файлового хранилища: {e}")
