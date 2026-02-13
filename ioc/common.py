from sqlalchemy.ext.asyncio import  AsyncSession, async_sessionmaker

from dishka import Provider, provide, Scope, from_context # type: ignore
from typing import AsyncGenerator
from application import common_interfaces
from infrastructure.db import repositories
from infrastructure import text_normalizer
from infrastructure.db import database
from config import Config
"""
ВАЖНО:
Все операции с БД в этом модуле потенциально могут:
- долго ждать блокировки (lock wait),
- упасть по statement_timeout / lock_timeout,
- завершиться ошибкой при обрыве соединения.

SQLAlchemy НЕ делает retry автоматически и НЕ восстанавливает транзакции.
Ошибки могут возникать на execute(), flush() или commit().

При доработке модуля обязательно:
- добавить обработку OperationalError / DBAPIError,
- делать rollback при ошибках,
- при необходимости реализовать retry на уровне бизнес-логики
  (ТОЛЬКО для идемпотентных операций).
"""

class ConfigProvider(Provider):
    config = from_context( scope=Scope.APP, provides=Config)

class DBProvider(Provider):
    
    engine = provide(staticmethod(database.new_engine), scope=Scope.APP, provides=database.AsyncEngine)

    sessionmaker = provide(staticmethod(database.new_session_maker), scope=Scope.APP, provides=async_sessionmaker[AsyncSession])
    
    @provide(scope=Scope.REQUEST, provides=AsyncSession)
    async def session(self, async_sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
        async with async_sessionmaker() as session:
            yield session
    
    


class RepositoryProvider(Provider):
    user_repository = provide(repositories.UserRepository, scope=Scope.REQUEST, provides=common_interfaces.UserRepository)
    project_repository = provide(repositories.ProjectRepository, scope=Scope.REQUEST, provides=common_interfaces.ProjectRepository)
    stage_repository = provide(repositories.StageRepository, scope=Scope.REQUEST, provides=common_interfaces.StageRepository)
    daily_log_repository = provide(repositories.DailyLogRepository, scope=Scope.REQUEST, provides=common_interfaces.DailyLogRepository)
    task_repository = provide(repositories.TaskRepository, scope=Scope.REQUEST, provides=common_interfaces.TaskRepository)
    subscription_repository = provide(repositories.SubscriptionRepository, scope=Scope.REQUEST, provides=common_interfaces.SubscriptionRepository)
    payment_repository = provide(repositories.PaymentRepository, scope=Scope.REQUEST, provides=common_interfaces.PaymentRepository)
    file_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.FileRepository)

class PaymentGatewayProvider(Provider):
    payment_gateway = provide(None, scope=Scope.REQUEST, provides=common_interfaces.PaymentGateway)

class LogerProvider(Provider):
    logger = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Logger)
    
class ClockProvider(Provider):
    clock = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Clock)
    
class TextNormalizerProvider(Provider):
    text_normalizer = provide(text_normalizer.TextNormalizer, scope=Scope.REQUEST, provides=common_interfaces.TextNormalizer)
    
