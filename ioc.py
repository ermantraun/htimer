from dishka import Provider, provide, Scope # type: ignore
from application import  common_interfaces
from application.user import interfaces as user_interfaces
from application.user import interactors
from application.user import validators


class DBProvider(Provider):
    """Провайдер для DB-подсистемы."""

    db_session = provide(None, scope=Scope.REQUEST, provides=common_interfaces.DBSession)


class UserProvider(Provider):
    """Провайдер для сервисов, связанных с пользователями."""
    hash_generator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.HashGenerator)
    user_creator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserCreator)
    user_updater = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserUpdater)
    user_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserGetter, override=True)
    user_context = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserContext)
    user_projects_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserProjectsGetter)
    projects_users_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.ProjectsUsersGetter)
    
    create_user_validator = provide(
        validators.CreateUserValidator,
        scope=Scope.REQUEST,
        provides=validators.CreateUserValidator,
    )
    
    create_user_interactor = provide(
        interactors.CreateUserInteractor,
        scope=Scope.REQUEST,
        provides=interactors.CreateUserInteractor,
    )


app: list[Provider] = [DBProvider(), UserProvider()]


