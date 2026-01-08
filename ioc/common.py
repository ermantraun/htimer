from dishka import Provider, provide, Scope # type: ignore
from application import common_interfaces


class DBProvider(Provider):
    db_session = provide(None, scope=Scope.REQUEST, provides=common_interfaces.DBSession)
