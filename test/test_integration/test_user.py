import dishka
import pytest
import pytest_asyncio
from typing import cast, Callable, AsyncGenerator
from enum import Enum
from uuid import uuid4
from ioc import app
import stubs
from application.user import interactors
from application.user import exceptions
from application.user import dto
from application import common_interfaces
from application.user import interfaces
from domain import entities


@pytest_asyncio.fixture(scope="module")
async def test_container() -> AsyncGenerator[dishka.AsyncContainer, None]:


    test_container = dishka.make_async_container(*app)

    yield test_container

    await test_container.close()


class CreateUserAuthScenario(Enum):
    HAS_PERMISSION = "has_permission"
    NO_PERMISSION = "no_permission"

def _make_create_dto(name: str, email: str, password: str, is_admin: bool =False):


    return dto.CreateUserInDTO(name=name, email=email, password=password,  is_admin=is_admin)


create_user_invalid_cases: list[tuple[Callable[[], dto.CreateUserInDTO], str, type[Exception], str, CreateUserAuthScenario]] = [
    # Name
    (
        lambda: _make_create_dto(cast(str, None), "user@example.com", "strongpass"),
        "No name",
        exceptions.InvalidNameError,
        r"Имя пользователя не может быть пустым\.",
        CreateUserAuthScenario.HAS_PERMISSION,
        
    ),
    (
        lambda: _make_create_dto("", "user@example.com", "strongpass"),
        "Empty name",
        exceptions.InvalidNameError,
        r"Имя пользователя не может быть пустым\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),
    (
        lambda: _make_create_dto("a" * 151, "user@example.com", "strongpass"),
        "Too long name",
        exceptions.InvalidNameError,
        r"Имя пользователя слишком длинное\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),

    # Email
    (
        lambda: _make_create_dto("User", cast(str, None), "strongpass"),
        "No email",
        exceptions.InvalidEmailError,
        r"Email не может быть пустым\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),
    (
        lambda: _make_create_dto("User", "invalid-email", "strongpass"),
        "Malformed email",
        exceptions.InvalidEmailError,
        r"Неверный формат email\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),
    (
        lambda: _make_create_dto("User", ("a" * 250) + "@example.com", "strongpass"),
        "Too long email",
        exceptions.InvalidEmailError,
        r"Email слишком длинный\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),

    # Password
    (
        lambda: _make_create_dto("User", "user@example.com", cast(str, None)),
        "No password",
        exceptions.InvalidPasswordError,
        r"Некорректный пароль\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),
    (
        lambda: _make_create_dto("User", "user@example.com", "short"),
        "Too short password",
        exceptions.InvalidPasswordError,
        r"Пароль должен быть не менее 8 символов\.",
        CreateUserAuthScenario.HAS_PERMISSION,
    ),

    # Permissions
    (
        lambda: _make_create_dto("User", "user2@example.com", "verystrongpass"),
        "No permission to create",
        exceptions.UserCannotCreateUsersError,
        r"Пользователь не имеет прав для создания других пользователей\.",
        CreateUserAuthScenario.NO_PERMISSION,
    ),
]

@pytest_asyncio.fixture(scope="function")
async def scenario(
    request: pytest.FixtureRequest,
) -> CreateUserAuthScenario:
    return request.param


@pytest_asyncio.fixture(scope="function")
async def create_user_interactor(
    scenario: CreateUserAuthScenario,
) -> interactors.CreateUserInteractor:

    current_uuid = uuid4()
    is_admin = scenario is CreateUserAuthScenario.HAS_PERMISSION

    current_user = entities.User(
        uuid=current_uuid,
        name="Current",
        email="current@example.com",
        password_hash="hashed:pw",
        creator_uuid=current_uuid,
        is_active=True,
        is_archived=False,
        is_admin=is_admin,
    )

    test_provider = dishka.Provider(scope=dishka.Scope.REQUEST)
    
    test_provider.provide(stubs.DummyDBSession, scope=dishka.Scope.REQUEST, provides=common_interfaces.DBSession)
    test_provider.provide(stubs.DummyHashGenerator, scope=dishka.Scope.REQUEST, provides=interfaces.HashGenerator)
    test_provider.provide(stubs.DummyUserCreator, scope=dishka.Scope.REQUEST, provides=interfaces.UserCreator)
    test_provider.provide(stubs.dummy_get_user_factory(current_user), scope=dishka.Scope.REQUEST, provides=interfaces.UserGetter)
    test_provider.provide(stubs.dummy_get_context_factory(current_uuid), scope=dishka.Scope.REQUEST, provides=interfaces.UserContext)

    test_container = dishka.make_async_container(test_provider, *app)

    
    async with test_container() as request_scope:
        
        return await request_scope.get(interactors.CreateUserInteractor)




@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data_factory, description, err, msg_regex, scenario",
    create_user_invalid_cases,
    indirect=['scenario'],
)
async def test_create_user_invalid(data_factory: Callable[[], dto.CreateUserInDTO], description: str, err: type[Exception], msg_regex: str, create_user_interactor: interactors.CreateUserInteractor):
    
    data = data_factory()
    with pytest.raises(err, match=msg_regex):
        await create_user_interactor.execute(data)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario",
    [CreateUserAuthScenario.HAS_PERMISSION],
    indirect=['scenario'],
)
async def test_create_user_valid(create_user_interactor: interactors.CreateUserInteractor):
    data = _make_create_dto("NewUser", "newuser@example.com", "verystrongpass")
    result = await create_user_interactor.execute(data)
    assert result.name == "NewUser"
    assert result.email == "newuser@example.com"
    
    
    
    