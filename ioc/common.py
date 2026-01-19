from dishka import Provider, provide, Scope # type: ignore
from application import common_interfaces
from infrastructure import text_normalizer

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
    db_session = provide(None, scope=Scope.REQUEST, provides=common_interfaces.DBSession)

class RepositoryProvider(Provider):
    user_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.UserRepository)
    project_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.ProjectRepository)
    stage_repository = provide(None, scope=Scope.REQUEST, provides=common_interfaces.StageRepository)

class LogerProvider(Provider):
    logger = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Logger)
    
class ClockProvider(Provider):
    clock = provide(None, scope=Scope.REQUEST, provides=common_interfaces.Clock)
    
class TextNormalizerProvider(Provider):
    text_normalizer = provide(text_normalizer.TextNormalizer, scope=Scope.REQUEST, provides=common_interfaces.TextNormalizer)
    
