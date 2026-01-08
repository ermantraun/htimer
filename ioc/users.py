"""IoC providers for Users bounded context."""
from dishka import Provider, provide, Scope
from application.user import interfaces as user_interfaces
from application.user import interactors
from application.user import validators
from infrastructure.user import policy


class UserProvider(Provider):
    """Provider for user-related dependencies."""
    
    # Infrastructure dependencies (provided as None - to be overridden by tests or real implementations)
    hash_generator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.HashGenerator)
    user_creator = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserCreator)
    user_updater = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserUpdater)
    user_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserGetter)
    user_context = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserContext)
    user_projects_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.UserProjectsGetter)
    projects_users_getter = provide(None, scope=Scope.REQUEST, provides=user_interfaces.ProjectsUsersGetter)
    
    # Authorization/Policy (Infrastructure implementation)
    user_authorization_policy = provide(
        policy.UserAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=user_interfaces.UserAuthorizationPolicy,
    )
    
    # Validators
    create_user_validator = provide(
        validators.CreateUserValidator,
        scope=Scope.REQUEST,
        provides=validators.CreateUserValidator,
    )
    
    update_user_validator = provide(
        validators.UpdateUserValidator,
        scope=Scope.REQUEST,
        provides=validators.UpdateUserValidator,
    )
    
    get_users_list_validator = provide(
        validators.GetUsersListValidator,
        scope=Scope.REQUEST,
        provides=validators.GetUsersListValidator,
    )
    
    # Interactors
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
