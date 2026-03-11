from htimer.application import common_exceptions


class ProjectRepositoryError(Exception):
    """Raised when there is an error in the project repository."""
    pass

class ProjectNotFoundError(ProjectRepositoryError):
    """Raised when a project is not found."""
    pass

class StageRepositoryError(Exception):
    """Raised when there is an error in the stage repository."""
    pass

class StageNotFoundError(StageRepositoryError):
    """Raised when a stage is not found."""
    pass

class StageAlreadyExistsError(StageRepositoryError):
    """Raised when a stage already exists."""
    pass

class ParentStageAlreadyHasMainSubStageError(StageRepositoryError):
    """Raised when a parent stage already has sub-stages."""
    pass

class StageAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с этапом."""

    def __init__(self, message: str = "Недостаточно прав для операции с этапом."):
        super().__init__(message)

class UserRepositoryError(Exception):
    """Raised when there is an error in the user repository."""
    pass

class UserNotFoundError(UserRepositoryError):
    """Raised when a user is not found."""
    pass

class StageValidationError(Exception):
    """Raised when there is a validation error for stage data."""
    pass

class InvalidStageNameError(StageValidationError):
    """Raised when the stage name is invalid."""
    pass

class InvalidStageDescriptionError(StageValidationError):
    """Raised when the stage description is invalid."""
    pass
class AllFieldsNoneError(StageValidationError):
    """Raised when all fields for updating a stage are None."""
    pass

class StageCantUpdateError(Exception):
    """Raised when a stage cannot be updated due to business logic constraints."""
    pass

class StageCantCreateError(Exception):
    """Raised when a stage cannot be created due to business logic constraints (e.g., inactive subscription)."""
    pass