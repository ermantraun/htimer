from htimer.application.stage import exceptions


class UserNotProjectMemberError(exceptions.StageAuthorizationError):
    """Ошибка авторизации: пользователь не является участником проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция с этапом доступна только участнику проекта."):
        super().__init__(message)

