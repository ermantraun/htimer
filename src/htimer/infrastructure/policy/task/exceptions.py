from htimer.application.task.exceptions import TaskAuthorizationError


class UserNotProjectMemberError(TaskAuthorizationError):
    """Ошибка авторизации: пользователь не является участником проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция с задачей доступна только участнику проекта."):
        super().__init__(message)
