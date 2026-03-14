from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from htimer.config import Config


async def new_engine(config: Config) -> AsyncEngine:
    psql_config = config.postgres

    database_uri = f"{psql_config.async_driver}://{psql_config.user}:{psql_config.password}@{psql_config.host}:{psql_config.port}/{psql_config.db}"

    engine = create_async_engine(
        database_uri,  # URL подключения к БД (dialect+driver://user:pass@host/db)
        pool_size=10,  # базовый размер пула: сколько соединений держим постоянно
        max_overflow=10,  # сколько временных соединений можно открыть сверх pool_size
        pool_timeout=10,  # сколько секунд ждать свободное соединение из пула
        pool_recycle=1800,  # пересоздавать соединения каждые 1800 сек (защита от idle-timeout БД)
        pool_pre_ping=True,  # проверять соединение перед выдачей (SELECT 1), защита от "битых" коннектов
        isolation_level="READ COMMITTED",  # уровень изоляции транзакций по умолчанию
        echo=False,  # логирование SQL (True — только для отладки)
    )

    return engine


async def new_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
    )
