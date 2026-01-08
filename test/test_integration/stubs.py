from uuid import UUID
from modules.users.domain.entities import User, Project
from modules.users.application.dto import UpdateUserInDTO
from modules.users.application import exceptions

from modules.users.application.interfaces import (
    UserCreator,
    UserUpdater,
    UserGetter,
    UserContext,
    HashGenerator,
    UserProjectsGetter,
    ProjectsUsersGetter,
)

from application.common_interfaces import DBSession




# =========================
# DB
# =========================

class DummyDBSession(DBSession):
    async def commit(self) -> None:
        return None


# =========================
# Security
# =========================

class DummyHashGenerator(HashGenerator):
    def generate(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"


# =========================
# Users persistence
# =========================

class DummyUserCreator(UserCreator):
    def __init__(self, db_session: DBSession):
        pass
        
    async def create(self, data: User) -> User:
        return data


class DummyUserCreatorReturns(UserCreator):
    """UserCreator that returns a specific result."""
    def __init__(self, db_session: DBSession, result: User | exceptions.UserRepositoryError):
        self._result = result
        
    async def create(self, data: User) -> User | exceptions.UserRepositoryError:
        if isinstance(self._result, Exception):
            return self._result
        return self._result


class DummyUserUpdater(UserUpdater):
    def __init__(self, db_session: DBSession):
        pass

    async def update(self, data: UpdateUserInDTO) -> User:
        # Stub that raises an error if called unexpectedly
        raise AssertionError(
            "DummyUserUpdater was called, but no specific behavior was configured. "
            "Use patch_user_updater_returns() to configure behavior."
        )


class DummyUserUpdaterReturns(UserUpdater):
    """UserUpdater that returns a specific result."""
    def __init__(self, db_session: DBSession, result: User | exceptions.UserRepositoryError):
        self._result = result

    async def update(self, data: UpdateUserInDTO) -> User | exceptions.UserRepositoryError:
        if isinstance(self._result, Exception):
            return self._result
        return self._result


class DummyUserGetterReturns(UserGetter):
    """UserGetter that returns a specific result for any UUID."""
    def __init__(self, db_session: DBSession, result: User | exceptions.UserRepositoryError):
        self._result = result
        
    async def get(self, user_uuid: UUID) -> User | exceptions.UserRepositoryError:
        if isinstance(self._result, Exception):
            return self._result
        return self._result


# =========================
# Projects
# =========================

class DummyUserProjectsGetter(UserProjectsGetter):
    def __init__(self, session: DBSession) -> None:
        pass
        
    async def get(self, user_uuid: UUID) -> set[Project]:
        return set()


class DummyUserProjectsGetterReturns(UserProjectsGetter):
    """UserProjectsGetter that returns a specific result."""
    def __init__(self, session: DBSession, result: set[Project] | exceptions.UserRepositoryError):
        self._result = result
        
    async def get(self, user_uuid: UUID) -> set[Project] | exceptions.UserRepositoryError:
        if isinstance(self._result, Exception):
            return self._result
        return self._result


class DummyProjectsUsersGetter(ProjectsUsersGetter):
    def __init__(self, session: DBSession) -> None:
        pass
        
    async def get(
        self,
        projects_uuid: list[UUID] | None,
        is_active: bool | None,
    ) -> list[User]:
        return []


class DummyProjectsUsersGetterReturns(ProjectsUsersGetter):
    """ProjectsUsersGetter that returns a specific result."""
    def __init__(self, session: DBSession, result: list[User] | exceptions.UserRepositoryError):
        self._result = result
        
    async def get(
        self,
        projects_uuid: list[UUID] | None,
        is_active: bool | None,
    ) -> list[User] | exceptions.UserRepositoryError:
        if isinstance(self._result, Exception):
            return self._result
        return self._result


def dummy_get_user_factory(
    user: User,
) -> type[UserGetter]:
    
    class DummyUserGetter(UserGetter):
        def __init__(self, db_session: DBSession):
            pass 
        
        async def get(self, user_uuid: UUID) -> User:
            if user_uuid != user.uuid:
                raise AssertionError(
                    f"Unexpected user_uuid: {user_uuid}, expected {user.uuid}"
                )
            return user
        
    return DummyUserGetter

def dummy_get_context_factory(
    user_uuid: UUID,
) -> type[UserContext]:
    
    class DummyUserContext(UserContext):
        def get_current_user_uuid(self) -> UUID:
            return user_uuid
        
    return DummyUserContext