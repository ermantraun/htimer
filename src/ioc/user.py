

from __future__ import annotations

from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore
from application.user import interactors, interfaces
from infrastructure.policy.user import policy
from infrastructure import hash_manager
from infrastructure.auth import auth

class SecurityProvider(Provider):
    hash_generator = provide(hash_manager.HashManager, scope=Scope.REQUEST, provides=interfaces.HashGenerator)
    hash_verifier = provide(hash_manager.HashManager, scope=Scope.REQUEST, provides=interfaces.HashVerifier)
    token_generator = provide(auth.Auth, scope=Scope.REQUEST, provides=interfaces.TokenGenerator)

class PolicyProvider(Provider):
    user_authorization_policy = provide(
        policy.UserAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.UserAuthorizationPolicy,
    )

class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateUserInteractor,
        interactors.UpdateUserInteractor,
        interactors.GetUsersListInteractor,
        interactors.ResetUserPasswordInteractor,
        interactors.LoginUserInteractor,
        scope=Scope.REQUEST
    )

class UserProvider(SecurityProvider, PolicyProvider, InteractorProvider):
    pass