from uuid import UUID
from domain.entities import User, Project
from application.user.dto import UpdateUserInDTO

from application.user.interfaces import (
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


class DummyUserUpdater(UserUpdater):
    def __init__(self, db_session: DBSession, updated_user: User | None = None):
        self._updated_user = updated_user

    async def update(self, data: UpdateUserInDTO) -> User:
        # стаб НЕ анализирует DTO
        # либо возвращает заранее подготовленного пользователя,
        # либо явно падает, если его использовать не планировали
        if self._updated_user is None:
            raise AssertionError(
                "DummyUserUpdater was called, but no updated_user was provided"
            )
        return self._updated_user


# =========================
# Projects
# =========================

class DummyUserProjectsGetter(UserProjectsGetter):
    def __init__(self, session: DBSession) -> None:
        pass
        
    async def get(self, user_uuid: UUID) -> set[Project]:
        return set()


class DummyProjectsUsersGetter(ProjectsUsersGetter):
    def __init__(self, session: DBSession) -> None:
        pass
        
    async def get(
        self,
        projects_uuid: list[UUID] | None,
        is_active: bool | None,
    ) -> list[User]:
        return []

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