class TaskAuthorizationError(Exception):
    """Raised when there is an authorization error related to tasks."""
    pass

class TaskValidationError(Exception):
    """Raised when task input is invalid."""
    pass


class CantCreateTask(Exception):
    """Raised when task cannot be created due to business rules (ensure_create)."""
    pass


class CantUpdateTask(Exception):
    """Raised when task cannot be updated due to business rules (ensure_update)."""
    pass


class InvalidTaskNameError(TaskValidationError):
    """Task name is invalid."""
    pass


class InvalidTaskDescriptionError(TaskValidationError):
    """Task description is invalid."""
    pass


class AllFieldsNoneError(TaskValidationError):
    """All fields for update are None."""
    pass
