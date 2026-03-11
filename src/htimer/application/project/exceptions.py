
from htimer.application import common_exceptions


class ProjectAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с проектом."""

    def __init__(self, message: str = "Недостаточно прав для операции с проектом."):
        super().__init__(message)

class ProjectValidationError(Exception):
    """Ошибки валидации данных проекта."""
    pass

class CantUpdateProjectError(ProjectValidationError):
    """Невозможно изменить заблокированный проект."""
    pass


class InvalidProjectNameError(ProjectValidationError):
    """Неверное имя проекта."""
    pass

class AllFieldsNoneError(ProjectValidationError):
    """Все поля для обновления отсутствуют."""
    pass

class InvalidProjectDescriptionError(ProjectValidationError):
    """Неверное описание проекта."""
    pass


