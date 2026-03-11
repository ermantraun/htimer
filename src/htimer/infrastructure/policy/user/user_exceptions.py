from htimer.application.user.exceptions import UserAuthorizationError


class AdminIsNotProjectOwner(UserAuthorizationError):
    """Ошибка авторизации: пользователь не имеет доступа к запрошенному проекту."""

    def __init__(self, message: str = "Недостаточно прав: доступ к запрошенному проекту запрещён."):
        super().__init__(message)

class UserIsNotAdmin(UserAuthorizationError):
    """Ошибка авторизации: пользователь не является администратором."""

    def __init__(self, message: str = "Недостаточно прав: операция доступна только администратору."):
        super().__init__(message)

class UserCannotCreateUsersError(UserAuthorizationError):
    """Ошибка авторизации: пользователь не может создавать других пользователей."""

    def __init__(self, message: str = "Недостаточно прав: создание пользователей запрещено."):
        super().__init__(message)


class CannotChangeSelfError(UserAuthorizationError):
    """Ошибка авторизации: запрещено изменять собственные привилегии."""

    def __init__(self, message: str = "Недостаточно прав: нельзя изменять собственные привилегии."):
        super().__init__(message)


class CannotChangeStatusSelfError(UserAuthorizationError):
    """Ошибка авторизации: запрещено изменять собственный статус аккаунта."""

    def __init__(self, message: str = "Недостаточно прав: нельзя изменять собственный статус аккаунта."):
        super().__init__(message)

class UserCannotUpdateUserError(UserAuthorizationError):
    """Ошибка авторизации: пользователь не может изменять целевого пользователя."""

    def __init__(self, message: str = "Недостаточно прав: изменение целевого пользователя запрещено."):
        super().__init__(message)

class CannotResetOwnPasswordError(UserAuthorizationError):
    """Ошибка авторизации: запрещено сбрасывать собственный пароль этим методом."""

    def __init__(self, message: str = "Недостаточно прав: нельзя сбрасывать собственный пароль этим методом."):
        super().__init__(message)

class UserCannotResetPasswordError(UserAuthorizationError):
    """Ошибка авторизации: пользователь не может сбрасывать пароль целевого пользователя."""

    def __init__(self, message: str = "Недостаточно прав: сброс пароля целевого пользователя запрещён."):
        super().__init__(message)

