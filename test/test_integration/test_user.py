"""
Tests for User interactors following consistent style guidelines:
- DI/Container only in fixtures, never in tests
- No indirect enum fixtures for scenarios
- Scenarios via patch/override callables
- InteractorPatch type for customization
- Parametrize only for DTO validation tables with ids
- Validation tested separately from RBAC/not-found/already-exists
- One test = one reason to fail
- Container guaranteed to close (no leaks)
"""
import pytest
from uuid import uuid4, UUID
from domain import entities
from application.user import interactors, dto, exceptions
from test.test_integration.test_helpers import (
    make_interactor,
    patch_current_user,
    patch_user_creator_returns,
)


# ============================================================================
# Helper factories for test data
# ============================================================================

def make_admin_user(uuid: UUID | None = None) -> entities.User:
    """Create an admin user for testing."""
    if uuid is None:
        uuid = uuid4()
    return entities.User(
        uuid=uuid,
        name="Admin User",
        email="admin@example.com",
        password_hash="hashed:password",
        creator_uuid=uuid,
        is_active=True,
        is_archived=False,
        is_admin=True,
    )


def make_regular_user(uuid: UUID | None = None) -> entities.User:
    """Create a regular (non-admin) user for testing."""
    if uuid is None:
        uuid = uuid4()
    return entities.User(
        uuid=uuid,
        name="Regular User",
        email="user@example.com",
        password_hash="hashed:password",
        creator_uuid=uuid,
        is_active=True,
        is_archived=False,
        is_admin=False,
    )


def make_create_user_dto(
    name: str = "NewUser",
    email: str = "newuser@example.com",
    password: str = "strongpassword",
    is_admin: bool = False,
    is_active: bool | None = True,
    is_archived: bool | None = False,
) -> dto.CreateUserInDTO:
    """Create a CreateUserInDTO with sensible defaults."""
    return dto.CreateUserInDTO(
        name=name,
        email=email,
        password=password,
        is_admin=is_admin,
        is_active=is_active,
        is_archived=is_archived,
    )


# ============================================================================
# CreateUserInteractor Tests
# ============================================================================

# --- Validation Tests (DTO field validation) ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,email,password,expected_error,expected_message",
    [
        # Name validation
        (None, "user@example.com", "strongpass", exceptions.InvalidNameError, r"Имя пользователя не может быть пустым\."),
        ("", "user@example.com", "strongpass", exceptions.InvalidNameError, r"Имя пользователя не может быть пустым\."),
        ("   ", "user@example.com", "strongpass", exceptions.InvalidNameError, r"Имя пользователя не может быть пустым\."),
        ("a" * 151, "user@example.com", "strongpass", exceptions.InvalidNameError, r"Имя пользователя слишком длинное\."),
        
        # Email validation
        ("User", None, "strongpass", exceptions.InvalidEmailError, r"Email не может быть пустым\."),
        ("User", "", "strongpass", exceptions.InvalidEmailError, r"Email не может быть пустым\."),
        ("User", "invalid-email", "strongpass", exceptions.InvalidEmailError, r"Неверный формат email\."),
        ("User", "a" * 250 + "@example.com", "strongpass", exceptions.InvalidEmailError, r"Email слишком длинный\."),
        
        # Password validation
        ("User", "user@example.com", None, exceptions.InvalidPasswordError, r"Некорректный пароль\."),
        ("User", "user@example.com", "short", exceptions.InvalidPasswordError, r"Пароль должен быть не менее 8 символов\."),
    ],
    ids=[
        "name_none",
        "name_empty",
        "name_whitespace",
        "name_too_long",
        "email_none",
        "email_empty",
        "email_malformed",
        "email_too_long",
        "password_none",
        "password_too_short",
    ]
)
async def test_create_user_validation_errors(name, email, password, expected_error, expected_message):
    """Test CreateUserInteractor DTO validation failures."""
    admin = make_admin_user()
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[patch_current_user(admin)]
    )
    
    try:
        data = make_create_user_dto(name=name, email=email, password=password)
        
        with pytest.raises(expected_error, match=expected_message):
            await interactor.execute(data)
    finally:
        await container.close()


# --- RBAC Tests (Role-Based Access Control) ---

@pytest.mark.asyncio
async def test_create_user_rbac_non_admin_cannot_create():
    """Test that non-admin users cannot create other users."""
    regular_user = make_regular_user()
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[patch_current_user(regular_user)]
    )
    
    try:
        data = make_create_user_dto()
        
        with pytest.raises(
            exceptions.UserCannotCreateUsersError,
            match=r"Пользователь не имеет прав для создания других пользователей\."
        ):
            await interactor.execute(data)
    finally:
        await container.close()


@pytest.mark.asyncio
async def test_create_user_rbac_admin_can_create():
    """Test that admin users can create other users."""
    admin = make_admin_user()
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[patch_current_user(admin)]
    )
    
    try:
        data = make_create_user_dto(
            name="NewUser",
            email="newuser@example.com",
            password="strongpassword"
        )
        
        result = await interactor.execute(data)
        
        assert result.name == "NewUser"
        assert result.email == "newuser@example.com"
        assert result.is_active is True
        assert result.is_archived is False
        assert result.is_admin is False
    finally:
        await container.close()


# --- Repository Error Tests ---

@pytest.mark.asyncio
async def test_create_user_already_exists_error():
    """Test CreateUserInteractor when email already exists."""
    admin = make_admin_user()
    error = exceptions.EmailAlreadyExistsError("Email already exists")
    
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[
            patch_current_user(admin),
            patch_user_creator_returns(error),
        ]
    )
    
    try:
        data = make_create_user_dto()
        
        with pytest.raises(exceptions.EmailAlreadyExistsError):
            await interactor.execute(data)
    finally:
        await container.close()


# --- Success Cases ---

@pytest.mark.asyncio
async def test_create_user_success_with_defaults():
    """Test successful user creation with default values."""
    admin = make_admin_user()
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[patch_current_user(admin)]
    )
    
    try:
        data = make_create_user_dto()
        result = await interactor.execute(data)
        
        assert result.name == "NewUser"
        assert result.email == "newuser@example.com"
        assert result.is_active is True
        assert result.is_archived is False
    finally:
        await container.close()


@pytest.mark.asyncio
async def test_create_user_success_with_custom_status():
    """Test successful user creation with custom status values."""
    admin = make_admin_user()
    interactor, container = await make_interactor(
        interactors.CreateUserInteractor,
        patches=[patch_current_user(admin)]
    )
    
    try:
        data = make_create_user_dto(
            name="InactiveUser",
            email="inactive@example.com",
            password="strongpassword",
            is_active=False,
            is_archived=True
        )
        result = await interactor.execute(data)
        
        assert result.name == "InactiveUser"
        assert result.is_active is False
        assert result.is_archived is True
    finally:
        await container.close()


# ============================================================================
# TODO: UpdateUserInteractor Tests
# ============================================================================
# Following same pattern:
# - Validation tests (parametrized with ids)
# - RBAC tests (separate from validation)
# - Not found tests
# - Already exists tests
# - Success cases

# ============================================================================
# TODO: GetUsersInteractor Tests
# ============================================================================
# Following same pattern:
# - Validation tests (parametrized with ids)
# - RBAC tests (separate from validation)
# - Success cases with various filters
    