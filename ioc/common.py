from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from dishka import Provider, provide, Scope # type: ignore
from typing import AsyncGenerator
from application import common_interfaces
from infrastructure import text_normalizer
from infrastructure.db import database

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

class DBProvider(Provider):
    
    async_sessionmaker = provide(database.async_sessionmaker, scope=Scope.APP, provides=async_sessionmaker[AsyncSession])
    
    @provide(scope=Scope.REQUEST, provides=AsyncSession)
    async def session(self, async_sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
        async with async_sessionmaker() as session:
            yield session
    


class RepositoryProvider(Provider):
    user_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.UserRepository)
    project_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.ProjectRepository)
    stage_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.StageRepository)
    daily_log_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.DailyLogRepository)
    file_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.FileRepository)
    task_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.TaskRepository)
    subscription_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.SubscriptionRepository)

class PaymentGatewayProvider(Provider):
    payment_gateway = provide(None, scope=Scope.REQUEST, provides=common_interfaces.PaymentGateway)

class LogerProvider(Provider):
    logger = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Logger)
    
class ClockProvider(Provider):
    clock = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Clock)
    
class TextNormalizerProvider(Provider):
    text_normalizer = provide(text_normalizer.TextNormalizer, scope=Scope.REQUEST, provides=common_interfaces.TextNormalizer)
    
