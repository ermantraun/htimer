from application.task.exceptions import TaskAuthorizationError

class UserNotProjectMemberError(TaskAuthorizationError):
    """Raised when user is not a member of the project."""
    pass
