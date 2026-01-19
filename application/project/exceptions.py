
class ProjectAuthorizationError(Exception):
    """Raised when a user is not authorized to perform a project-related action."""
    pass

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


