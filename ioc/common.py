"""Common IoC providers for shared infrastructure."""
from dishka import Provider, provide, Scope
from application import common_interfaces


class DBProvider(Provider):
    """Provider for DB-related dependencies."""

    db_session = provide(None, scope=Scope.REQUEST, provides=common_interfaces.DBSession)
