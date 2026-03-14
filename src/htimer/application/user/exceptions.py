from htimer.application import common_exceptions


class UserValidationError(Exception):
    """Ошибка валидации данных пользователя."""

    pass


class InvalidNameError(UserValidationError):
    """Ошибка некорректного имени пользователя."""

    pass


class InvalidEmailError(UserValidationError):
    """Ошибка некорректного email пользователя."""

    pass


class InvalidCredentialsError(Exception):
    """Ошибка: неверные учетные данные."""

    pass


class InvalidPasswordError(UserValidationError):
    """Ошибка некорректного пароля пользователя."""

    pass


class UserAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с пользователем."""

    def __init__(
        self, message: str = "Недостаточно прав для операции с пользователем."
    ):
        super().__init__(message)


class InvalidPasswordHashError(Exception):
    """Ошибка: некорректный хеш пароля."""

    pass


class CantResetPasswordError(Exception):
    """Ошибка: сброс пароля невозможен."""

    pass


class CantUpdatePasswordError(Exception):
    """Ошибка: обновление пароля невозможно."""

    pass


class CantUpdateError(Exception):
    """Ошибка: обновление пользователя невозможно."""

    pass
