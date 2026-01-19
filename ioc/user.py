

from __future__ import annotations

from dishka import Provider, Scope, provide, AnyOf # type: ignore
from application.user import interactors, interfaces
from infrastructure.policy.user import policy

    


class UserProvider(Provider):
    token_generator = provide(None, scope=Scope.REQUEST, provides=interfaces.TokenGenerator)
    
    hash_manager = provide(None, scope=Scope.REQUEST, provides=AnyOf[interfaces.HashGenerator, interfaces.HashVerifier])
    user_authorization_policy = provide(
        policy.UserAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=[interfaces.UserCreateAuthorizationPolicy, interfaces.UserUpdateAuthorizationPolicy, 
                  interfaces.UserPasswordResetAuthorizationPolicy, interfaces.UsersListAuthorizationPolicy],
    )

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
        interactors.GetUsersListInteractor,
        scope=Scope.REQUEST,
        provides=interactors.GetUsersListInteractor,
    )

    reset_user_password_interactor = provide(
        interactors.ResetUserPasswordInteractor,
        scope=Scope.REQUEST,
        provides=interactors.ResetUserPasswordInteractor,
    )
    
