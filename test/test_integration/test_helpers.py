"""
Shared test infrastructure for interactor testing.

This module provides:
- InteractorPatch type for scenario customization
- Patch helper functions for common test scenarios
- Fixture factory for creating interactors with custom patches
"""
from typing import Callable,  Type, TypeVar
from uuid import UUID
import dishka
from domain import entities
from application.user import interfaces, exceptions
from application import common_interfaces


# Type alias for patch functions
InteractorPatch = Callable[[dishka.Provider, dict], None]

T = TypeVar('T')


async def make_interactor(
    interactor_type: Type[T],
    patches: list[InteractorPatch] | None = None,
) -> tuple[T, dishka.AsyncContainer]:
    """
    Create an interactor with custom patches applied.
    
    Args:
        interactor_type: The interactor class to instantiate
        patches: List of patch functions to apply (optional)
    
    Returns:
        Tuple of (interactor instance, container)
        The container must be closed after use with: await container.close()
    
    Usage:
        patches = [patch_current_user(admin_user)]
        interactor, container = await make_interactor(CreateUserInteractor, patches)
        try:
            result = await interactor.execute(dto)
        finally:
            await container.close()
    """
    from ioc import get_providers
    from test.test_integration import stubs
    
    # Create a test provider with default stubs
    test_provider = dishka.Provider(scope=dishka.Scope.REQUEST)
    
    # Provide default implementations for ALL dependencies
    test_provider.provide(stubs.DummyDBSession, scope=dishka.Scope.REQUEST, provides=common_interfaces.DBSession)
    test_provider.provide(stubs.DummyHashGenerator, scope=dishka.Scope.REQUEST, provides=interfaces.HashGenerator)
    test_provider.provide(stubs.DummyUserCreator, scope=dishka.Scope.REQUEST, provides=interfaces.UserCreator)
    test_provider.provide(stubs.DummyUserUpdater, scope=dishka.Scope.REQUEST, provides=interfaces.UserUpdater)
    test_provider.provide(stubs.DummyUserProjectsGetter, scope=dishka.Scope.REQUEST, provides=interfaces.UserProjectsGetter)
    test_provider.provide(stubs.DummyProjectsUsersGetter, scope=dishka.Scope.REQUEST, provides=interfaces.ProjectsUsersGetter)
    
    # Apply custom patches
    context: dict = {}
    if patches:
        for patch in patches:
            patch(test_provider, context)
    
    # Create container with test provider FIRST, then app providers
    # This ensures test overrides take precedence
    container = dishka.make_async_container(test_provider, *get_providers())
    
    # Get the interactor from a request scope
    async with container() as request_scope:
        interactor = await request_scope.get(interactor_type)
    
    # Return interactor and container (caller must close container)
    return interactor, container


def patch_current_user_uuid(uuid: UUID) -> InteractorPatch:
    """Patch UserContext to return a specific UUID."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import dummy_get_context_factory
        provider.provide(
            dummy_get_context_factory(uuid),
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserContext
        )
    return patch


def patch_current_user(user: entities.User) -> InteractorPatch:
    """Patch UserContext and UserGetter to return a specific current user."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import dummy_get_context_factory, dummy_get_user_factory
        provider.provide(
            dummy_get_context_factory(user.uuid),
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserContext
        )
        provider.provide(
            dummy_get_user_factory(user),
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserGetter
        )
        # Store for test access
        context['current_user'] = user
    return patch


def patch_user_getter_returns(user: entities.User | exceptions.UserRepositoryError) -> InteractorPatch:
    """Patch UserGetter to return a specific user or error."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import DummyUserGetterReturns
        def factory(session: common_interfaces.DBSession) -> interfaces.UserGetter:
            return DummyUserGetterReturns(session, user)
        provider.provide(
            factory,
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserGetter
        )
    return patch


def patch_user_creator_returns(result: entities.User | exceptions.UserRepositoryError) -> InteractorPatch:
    """Patch UserCreator to return a specific result or error."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import DummyUserCreatorReturns
        def factory(session: common_interfaces.DBSession) -> interfaces.UserCreator:
            return DummyUserCreatorReturns(session, result)
        provider.provide(
            factory,
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserCreator
        )
    return patch


def patch_user_updater_returns(result: entities.User | exceptions.UserRepositoryError) -> InteractorPatch:
    """Patch UserUpdater to return a specific result or error."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import DummyUserUpdaterReturns
        def factory(session: common_interfaces.DBSession) -> interfaces.UserUpdater:
            return DummyUserUpdaterReturns(session, result)
        provider.provide(
            factory,
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserUpdater
        )
    return patch


def patch_user_projects_getter_returns(projects: set[entities.Project] | exceptions.UserRepositoryError) -> InteractorPatch:
    """Patch UserProjectsGetter to return specific projects or error."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import DummyUserProjectsGetterReturns
        def factory(session: common_interfaces.DBSession) -> interfaces.UserProjectsGetter:
            return DummyUserProjectsGetterReturns(session, projects)
        provider.provide(
            factory,
            scope=dishka.Scope.REQUEST,
            provides=interfaces.UserProjectsGetter
        )
    return patch


def patch_projects_users_getter_returns(users: list[entities.User] | exceptions.UserRepositoryError) -> InteractorPatch:
    """Patch ProjectsUsersGetter to return specific users or error."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        from test.test_integration.stubs import DummyProjectsUsersGetterReturns
        def factory(session: common_interfaces.DBSession) -> interfaces.ProjectsUsersGetter:
            return DummyProjectsUsersGetterReturns(session, users)
        provider.provide(
            factory,
            scope=dishka.Scope.REQUEST,
            provides=interfaces.ProjectsUsersGetter
        )
    return patch


def combine_patches(*patches: InteractorPatch) -> InteractorPatch:
    """Combine multiple patches into one."""
    def patch(provider: dishka.Provider, context: dict) -> None:
        for p in patches:
            p(provider, context)
    return patch
