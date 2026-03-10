
import minio
from datetime import timedelta
from domain.entities import DailyLogFile
from infrastructure.repositories import interfaces, exceptions
from config import Config
import asyncio

class FileRepository(interfaces.StorageFileRepository):
    

    def __init__(self, client: minio.Minio, config: Config):
        self.client = client
        self.bucket_name = config.minio.bucket_name
        self.loop = asyncio.get_event_loop()

    async def get_upload_link(self, file: DailyLogFile) -> str | exceptions.FileRepositoryError:
        
        def _get_upload_link():
            return self.client.presigned_put_object(
                bucket_name=self.bucket_name,
                object_name=str(file.uuid),
                expires=timedelta(minutes=15)
            )
        try:
            return await self.loop.run_in_executor(None, _get_upload_link)
        except minio.S3Error as e:
            return exceptions.FileRepositoryError(str(e))
    
    async def get_unload_link(self, file: DailyLogFile) -> str | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        def _get_unload_link():
            return self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=str(file.uuid),
                    expires=timedelta(minutes=15)
                )
        
        try:
            return await self.loop.run_in_executor(None, _get_unload_link)
        except minio.S3Error as e:
            if e.code == 'NoSuchKey':
                return exceptions.FileNotFoundError(f"File with uuid {file.uuid} not found")
            return exceptions.FileRepositoryError(str(e))
    
    async def get_unload_link_list(self, files: list[DailyLogFile]) -> list[tuple[DailyLogFile, str]] | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        
        def _get_unload_link_list(file: DailyLogFile):
            link = self.client.presigned_get_object(
                        bucket_name=self.bucket_name,
                        object_name=str(file.uuid),
                        expires=timedelta(minutes=15)
                    )
            return (file, link)
        try:
            tasks = [self.loop.run_in_executor(None, _get_unload_link_list, file) for file in files]
            return await asyncio.gather(*tasks)
        except minio.S3Error as e:
            if e.code == 'NoSuchKey':
                return exceptions.FileNotFoundError(f"One or more files not found")
            return exceptions.FileRepositoryError(str(e))

    
    async def get_remove_link(self, file: DailyLogFile) -> None | exceptions.FileRepositoryError | exceptions.FileNotFoundError:
        
        def _get_remove_link():
            self.client.remove_object(
                    bucket_name=self.bucket_name,
                    object_name=str(file.uuid)
                )
        
        try:
            await self.loop.run_in_executor(None, _get_remove_link)
        except minio.S3Error as e:
            if e.code == 'NoSuchKey':
                return exceptions.FileNotFoundError(f"File with uuid {file.uuid} not found")
            return exceptions.FileRepositoryError(str(e))
    


    
