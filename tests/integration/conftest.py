# pyright: reportUnusedFunction=false
from collections.abc import AsyncGenerator
from typing import Any

import dishka
import pytest_asyncio
from dishka import AsyncContainer  # type: ignore
from sqlalchemy import event
from sqlalchemy.exc import ResourceClosedError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session, SessionTransaction

from htimer.application import common_interfaces
from htimer.application.user import interfaces as user_interfaces
from htimer.config import Config, PostgresConfig
from htimer.infrastructure.db import repositories as db_repositories
from htimer.infrastructure.db.models import Base
from htimer.infrastructure.repositories import interfaces as repository_interfaces
from htimer.ioc import common, user


@pytest_asyncio.fixture(scope="session")
async def test_config() -> Config:
    config = Config()
    config.postgres = PostgresConfig(
        user="admin",
        password="899595",
        host="localhost",
        port=5432,
        db="test_db",
        debug=True,
    )

    return config


@pytest_asyncio.fixture(scope="session")
async def app_container(test_config: Config) -> AsyncGenerator[AsyncContainer]:
    config = test_config
    container = dishka.make_async_container(
        common.CommonProvider(), user.SecurityProvider(), context={Config: config}
    )
    try:
        yield container
    finally:
        await container.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db(app_container: AsyncContainer) -> AsyncGenerator[None]:
    engine = await app_container.get(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def request_container(
    app_container: AsyncContainer,
) -> AsyncGenerator[Any]:
    async with app_container() as scope:
        yield scope


@pytest_asyncio.fixture(scope="function")
async def db_session(
    request_container: Any,
) -> AsyncGenerator[AsyncSession]:
    session = await request_container.get(AsyncSession)
    trans = await session.begin()
    await session.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(session: Session, transaction: SessionTransaction) -> None:
        if transaction.nested and not transaction._parent.nested:  # type: ignore[attr-defined, protected-access]
            session.begin_nested()

    try:
        yield session
    finally:
        try:
            if getattr(trans, "is_active", False):
                await trans.rollback()
        except ResourceClosedError:
            pass


@pytest_asyncio.fixture(scope="function")
async def user_repository(
    request_container: Any,
) -> repository_interfaces.DBUserRepository:
    return await request_container.get(repository_interfaces.DBUserRepository)


@pytest_asyncio.fixture(scope="function")
async def project_repository(
    request_container: Any,
) -> repository_interfaces.DBProjectRepository:
    return await request_container.get(repository_interfaces.DBProjectRepository)


@pytest_asyncio.fixture(scope="function")
async def stage_repository(
    request_container: Any,
) -> repository_interfaces.DBStageRepository:
    return await request_container.get(repository_interfaces.DBStageRepository)


@pytest_asyncio.fixture(scope="function")
async def daily_log_repository(
    request_container: Any,
) -> repository_interfaces.DBDailyLogRepository:
    return await request_container.get(repository_interfaces.DBDailyLogRepository)


@pytest_asyncio.fixture(scope="function")
async def task_repository(
    request_container: Any,
) -> repository_interfaces.DBTaskRepository:
    return await request_container.get(repository_interfaces.DBTaskRepository)


@pytest_asyncio.fixture(scope="function")
async def payment_repository(
    request_container: Any,
) -> repository_interfaces.DBPaymentRepository:
    return await request_container.get(repository_interfaces.DBPaymentRepository)


@pytest_asyncio.fixture(scope="function")
async def subscription_repository(
    request_container: Any,
) -> repository_interfaces.DBSubscriptionRepository:
    return await request_container.get(repository_interfaces.DBSubscriptionRepository)


@pytest_asyncio.fixture(scope="function")
async def db_file_repository(
    db_session: AsyncSession,
    test_config: Config,
) -> repository_interfaces.DBFileRepository:
    return db_repositories.FileRepository(db_session, test_config)


@pytest_asyncio.fixture(scope="function")
async def main_user_repository(
    request_container: Any,
) -> common_interfaces.UserRepository:
    return await request_container.get(common_interfaces.UserRepository)


@pytest_asyncio.fixture(scope="function")
async def main_project_repository(
    request_container: Any,
) -> common_interfaces.ProjectRepository:
    return await request_container.get(common_interfaces.ProjectRepository)


@pytest_asyncio.fixture(scope="function")
async def main_stage_repository(
    request_container: Any,
) -> common_interfaces.StageRepository:
    return await request_container.get(common_interfaces.StageRepository)


@pytest_asyncio.fixture(scope="function")
async def main_daily_log_repository(
    request_container: Any,
) -> common_interfaces.DailyLogRepository:
    return await request_container.get(common_interfaces.DailyLogRepository)


@pytest_asyncio.fixture(scope="function")
async def main_task_repository(
    request_container: Any,
) -> common_interfaces.TaskRepository:
    return await request_container.get(common_interfaces.TaskRepository)


@pytest_asyncio.fixture(scope="function")
async def main_payment_repository(
    request_container: Any,
) -> common_interfaces.PaymentRepository:
    return await request_container.get(common_interfaces.PaymentRepository)


@pytest_asyncio.fixture(scope="function")
async def main_subscription_repository(
    request_container: Any,
) -> common_interfaces.SubscriptionRepository:
    return await request_container.get(common_interfaces.SubscriptionRepository)


@pytest_asyncio.fixture(scope="function")
async def infra_clock(
    request_container: Any,
) -> common_interfaces.Clock:
    return await request_container.get(common_interfaces.Clock)


@pytest_asyncio.fixture(scope="function")
async def infra_logger(
    request_container: Any,
) -> common_interfaces.Logger:
    return await request_container.get(common_interfaces.Logger)


@pytest_asyncio.fixture(scope="function")
async def infra_text_normalizer(
    request_container: Any,
) -> common_interfaces.TextNormalizer:
    return await request_container.get(common_interfaces.TextNormalizer)


@pytest_asyncio.fixture(scope="function")
async def infra_payment_gateway(
    request_container: Any,
) -> common_interfaces.PaymentGateway:
    return await request_container.get(common_interfaces.PaymentGateway)


@pytest_asyncio.fixture(scope="function")
async def infra_hash_generator(
    request_container: Any,
) -> user_interfaces.HashGenerator:
    return await request_container.get(user_interfaces.HashGenerator)


@pytest_asyncio.fixture(scope="function")
async def infra_hash_verifier(
    request_container: Any,
) -> user_interfaces.HashVerifier:
    return await request_container.get(user_interfaces.HashVerifier)


@pytest_asyncio.fixture(scope="function")
async def infra_auth_context(
    request_container: Any,
) -> common_interfaces.Context:
    return await request_container.get(common_interfaces.Context)


@pytest_asyncio.fixture(scope="function")
async def infra_auth_token_generator(
    request_container: Any,
) -> user_interfaces.TokenGenerator:
    return await request_container.get(user_interfaces.TokenGenerator)
