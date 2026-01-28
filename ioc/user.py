

from __future__ import annotations

from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore
from application.user import interactors, interfaces
from infrastructure.policy.user import policy

    


class UserProvider(Provider):
    token_generator = provide(None, scope=Scope.REQUEST, provides=interfaces.TokenGenerator)
    
    hash_manager = provide(None, scope=Scope.REQUEST, provides=AnyOf[interfaces.HashGenerator, interfaces.HashVerifier])
    user_authorization_policy = provide(
        policy.UserAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.UserAuthorizationPolicy,
    )

    interactors = provide_all(
        interactors.CreateUserInteractor,
        interactors.UpdateUserInteractor,
        interactors.GetUsersListInteractor,
        interactors.ResetUserPasswordInteractor,
        interactors.LoginUserInteractor,
        scope=Scope.REQUEST
    )