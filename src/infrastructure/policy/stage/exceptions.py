from application.stage import exceptions


class UserNotProjectMemberError(exceptions.StageAuthorizationError):
    """Ошибка: пользователь не является участником проекта."""
    pass

