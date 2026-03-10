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

class UserAuthorizationError(Exception):
    """Ошибка авторизации пользователя."""
    pass

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