# pyright: reportUnusedFunction=false
from typing import Any, AsyncGenerator
import dishka
from dishka import AsyncContainer
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import Session, SessionTransaction

from infrastructure.db.models import Base
from application import common_interfaces
from config import Config, PostgresConfig
from ioc import common


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
async def app_container(test_config: Config) -> AsyncGenerator[AsyncContainer, None]:
    config = test_config
    container = dishka.make_async_container(
        common.ConfigProvider(),
        common.DBProvider(),
        common.RepositoryProvider(),
        context={Config: config},
    )
    try:
        yield container
    finally:
        await container.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db(app_container: AsyncContainer) -> AsyncGenerator[None, None]:
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
) -> AsyncGenerator[Any, None]:
    async with app_container() as scope:
        yield scope


@pytest_asyncio.fixture(scope="function")
async def db_session(
    request_container: Any,
) -> AsyncGenerator[AsyncSession, None]:
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
        await trans.rollback()


@pytest_asyncio.fixture(scope="function")
async def user_repository(
    request_container: Any,
) -> common_interfaces.UserRepository:
    return await request_container.get(common_interfaces.UserRepository)


@pytest_asyncio.fixture(scope="function")
async def project_repository(
    request_container: Any,
) -> common_interfaces.ProjectRepository:
    return await request_container.get(common_interfaces.ProjectRepository)


@pytest_asyncio.fixture(scope="function")
async def stage_repository(
    request_container: Any,
) -> common_interfaces.StageRepository:
    return await request_container.get(common_interfaces.StageRepository)


@pytest_asyncio.fixture(scope="function")
async def daily_log_repository(
    request_container: Any,
) -> common_interfaces.DailyLogRepository:
    return await request_container.get(common_interfaces.DailyLogRepository)


@pytest_asyncio.fixture(scope="function")
async def task_repository(
    request_container: Any,
) -> common_interfaces.TaskRepository:
    return await request_container.get(common_interfaces.TaskRepository)


@pytest_asyncio.fixture(scope="function")
async def payment_repository(
    request_container: Any,
) -> common_interfaces.PaymentRepository:
    return await request_container.get(common_interfaces.PaymentRepository)


@pytest_asyncio.fixture(scope="function")
async def subscription_repository(
    request_container: Any,
) -> common_interfaces.SubscriptionRepository:
    return await request_container.get(common_interfaces.SubscriptionRepository)
