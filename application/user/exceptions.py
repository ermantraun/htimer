


class UserValidationError(Exception):
    """Ошибка валидации данных пользователя."""
    pass

class InvalidNameError(UserValidationError):
    """Ошибка некорректного имени пользователя."""
    pass

class InvalidEmailError(UserValidationError):
    """Ошибка некорректного email пользователя."""
    pass

class InvalidPasswordError(UserValidationError):
    """Ошибка некорректного пароля пользователя."""
    pass

class UserRepositoryError(Exception):
    """Ошибка репозитория пользователя."""
    pass

class EmailAlreadyExistsError(UserRepositoryError):
    """Ошибка: пользователь уже существует."""
    pass


class UserNotFoundError(UserRepositoryError):
    """Ошибка: пользователь не найден."""
    pass

class InvalidToken(Exception):
    """Ошибка: недействительный токен."""
    pass

class InvalidPasswordHashError(Exception):
    """Ошибка: некорректный хеш пароля."""
    pass

class AdminIsNotProjectOwner(UserValidationError):
    """Ошибка: администратор не состоит в проекте."""
    pass

class UserIsNotAdmin(UserValidationError):
    """Ошибка: пользователь не является администратором."""
    pass

class UserCannotCreateUsersError(UserValidationError):
    """Ошибка: пользователь не имеет прав на создание других пользователей."""
    pass


# Ошибки, специфичные для валидации операций обновления
class CannotChangeAdminSelfError(UserValidationError):
    """Попытка самим себе повысить/понизить флаг администратора."""
    pass

class CannotChangeStatusSelfError(UserValidationError):
    """Попытка самим себе изменить активность/архивность аккаунта."""
    pass