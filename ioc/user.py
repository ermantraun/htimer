

from __future__ import annotations

from dishka import Provider, Scope, provide # type: ignore

from application.user import interactors, interfaces as user_interfaces, validators
from infrastructure.policy import user as user_policy


class UserProvider(Provider):

    hash_generator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.HashGenerator)
    user_creator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserCreator)
    user_updater = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserUpdater)
    user_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserGetter)
    user_context = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserContext)
    user_projects_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserProjectsGetter)
    projects_users_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.ProjectsUsersGetter)

    user_authorization_policy = provide(
        user_policy.UserAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=user_interfaces.UserAuthorizationPolicy,
    )

    create_user_validator = provide(validators.CreateUserValidator, scope=Scope.REQUEST)
    update_user_validator = provide(validators.UpdateUserValidator, scope=Scope.REQUEST)
    get_users_list_validator = provide(validators.GetUsersListValidator, scope=Scope.REQUEST)

    create_user_interactor = provide(
        interactors.CreateUserInteractor,
        scope=Scope.REQUEST,
        provides=interactors.CreateUserInteractor,
    )
    update_user_interactor = provide(
        interactors.UpdateUserInteractor,
        scope=Scope.REQUEST,
        provides=interactors.UpdateUserInteractor,
    )
    get_users_interactor = provide(
        interactors.GetUsersInteractor,
        scope=Scope.REQUEST,
        provides=interactors.GetUsersInteractor,
    )
