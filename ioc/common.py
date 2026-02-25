from sqlalchemy.ext.asyncio import  AsyncSession, async_sessionmaker
import minio
import aio_pika
from dishka import Provider, provide, Scope, from_context, AnyOf # type: ignore
from typing import AsyncGenerator
from application import common_interfaces
from infrastructure.db import repositories as db_repositories
from infrastructure import text_normalizer
from infrastructure import clock
from infrastructure.repositories import repositories
from infrastructure.auth import auth
from infrastructure.repositories import interfaces as repository_interfaces
from infrastructure.db import database
from infrastructure.logger import logger, interfaces as logger_interfaces
from infrastructure.auth import interfaces as auth_interfaces
from infrastructure.file_storage import repositories as storage_repository
from infrastructure.payment_gateway import gateway as payment_gateway
from config import Config, ClockConfig

class ConfigProvider(Provider):
    config = from_context( scope=Scope.APP, provides=Config)

    @provide(scope=Scope.APP, provides=ClockConfig)
    def clock_config(self, config: Config) -> ClockConfig:
        return config.clock_config

class StorageProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=minio.Minio)
    async def minio_client(self, config: Config) -> minio.Minio:
        return minio.Minio(
            endpoint=f"{config.minio.host}:{config.minio.port}",
            access_key=config.minio.access_key,
            secret_key=config.minio.secret_key,
            secure=False,
        )
    
class DBProvider(Provider):
    
    engine = provide(staticmethod(database.new_engine), scope=Scope.APP, provides=database.AsyncEngine)

    sessionmaker = provide(staticmethod(database.new_session_maker), scope=Scope.APP, provides=async_sessionmaker[AsyncSession])
    
    @provide(scope=Scope.REQUEST, provides=AsyncSession)
    async def session(self, async_sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
        async with async_sessionmaker() as session:
            yield session
class RepositoryProvider(Provider):
    
    db_user_repository = provide(db_repositories.UserRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBUserRepository)
    db_project_repository = provide(db_repositories.ProjectRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBProjectRepository)
    db_stage_repository = provide(db_repositories.StageRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBStageRepository)
    db_daily_log_repository = provide(db_repositories.DailyLogRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBDailyLogRepository)
    db_task_repository = provide(db_repositories.TaskRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBTaskRepository)
    db_subscription_repository = provide(db_repositories.SubscriptionRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBSubscriptionRepository)
    db_payment_repository = provide(db_repositories.PaymentRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBPaymentRepository)
    db_file_repository = provide(db_repositories.FileRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBFileRepository)
    file_storage_repository = provide(storage_repository.FileRepository, scope=Scope.REQUEST, provides=repository_interfaces.StorageFileRepository)
    db_report_repository = provide(db_repositories.ReportRepository, scope=Scope.REQUEST, provides=repository_interfaces.DBReportRepository)

    user_repository = provide(repositories.UserRepository, scope=Scope.REQUEST, provides=common_interfaces.UserRepository)
    project_repository = provide(repositories.ProjectRepository, scope=Scope.REQUEST, provides=common_interfaces.ProjectRepository)
    stage_repository = provide(repositories.StageRepository, scope=Scope.REQUEST, provides=common_interfaces.StageRepository)
    daily_log_repository = provide(repositories.DailyLogRepository, scope=Scope.REQUEST, provides=common_interfaces.DailyLogRepository)
    task_repository = provide(repositories.TaskRepository, scope=Scope.REQUEST, provides=common_interfaces.TaskRepository)
    subscription_repository = provide(repositories.SubscriptionRepository, scope=Scope.REQUEST, provides=common_interfaces.SubscriptionRepository)
    payment_repository = provide(repositories.PaymentRepository, scope=Scope.REQUEST, provides=common_interfaces.PaymentRepository)
    file_repository = provide(repositories.FileRepository, scope=Scope.REQUEST, provides=common_interfaces.FileRepository)
    report_repository = provide(repositories.ReportRepository, scope=Scope.REQUEST, provides=common_interfaces.ReportRepository)
class PaymentGatewayProvider(Provider):
    payment_gateway = provide(payment_gateway.YooKassaGateway, scope=Scope.REQUEST, provides=common_interfaces.PaymentGateway)

class LogerProvider(Provider):
    logger = provide(logger.Logger, scope=Scope.REQUEST, provides=common_interfaces.Logger)
    
class ClockProvider(Provider):
    clock = provide(clock.SystemClock, scope=Scope.REQUEST, provides=AnyOf[common_interfaces.Clock, logger_interfaces.Clock, auth_interfaces.Clock])

class TextNormalizerProvider(Provider):
    text_normalizer = provide(text_normalizer.TextNormalizer, scope=Scope.REQUEST, provides=common_interfaces.TextNormalizer)
    
class Auth(Provider):
    auth = provide(auth.Auth, scope=Scope.REQUEST, provides=common_interfaces.Context)

class RabbitMQProvider(Provider):

    @provide(scope=Scope.APP, provides=aio_pika.abc.AbstractConnection)
    async def connection(self, config: Config) -> aio_pika.abc.AbstractConnection:
        return await aio_pika.connect(
            host=config.rabbitmq.host,
            port=config.rabbitmq.port,
            login=config.rabbitmq.username,
            password=config.rabbitmq.password,
            heartbeat=config.rabbitmq.heartbeat,
            blocked_connection_timeout=config.rabbitmq.blocked_connection_timeout,
            connection_attempts=config.rabbitmq.connection_attempts,
            retry_delay=config.rabbitmq.retry_delay,
            socket_timeout=config.rabbitmq.socket_timeout
        )
    
    @provide(scope=Scope.REQUEST, provides=aio_pika.abc.AbstractChannel)
    async def channel(self, connection: aio_pika.abc.AbstractConnection, config: Config) -> aio_pika.abc.AbstractChannel:
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=config.rabbitmq.prefetch_count)
            return channel

class CommonProvider(ConfigProvider, StorageProvider, DBProvider, RepositoryProvider, PaymentGatewayProvider, LogerProvider, ClockProvider, TextNormalizerProvider, Auth):
    pass


