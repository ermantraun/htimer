class InvalidToken(Exception):
    """Ошибка: недействительный токен."""
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

class ProjectRepositoryError(Exception):
    """Raised when there is an error in the project repository."""
    pass

class UserAlreadyHasProjectError(ProjectRepositoryError):
    """Raised when a user already has a project and tries to create another one."""
    pass

class ProjectNotFoundError(ProjectRepositoryError):
    """Raised when a project is not found."""
    pass

class UserNotProjectMemberError(ProjectRepositoryError):
    """Raised when a user is not in the project members."""
    pass

class UserAlreadyProjectMemberError(ProjectRepositoryError):
    """Raised when a user is already a member of the project."""
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

class DailyLogRepositoryError(Exception):
    """Raised when there is an error in the daily log repository."""
    pass

class DailyLogAlreadyExistsError(DailyLogRepositoryError):
    """Raised when a daily log already exists for the given criteria."""
    pass

class DailyLogNotFoundError(DailyLogRepositoryError):
    """Raised when a daily log is not found."""
    pass

class InvalidDate(Exception):
    """Raised when a provided date is invalid."""
    pass