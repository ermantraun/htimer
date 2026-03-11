from htimer.application.daily_log.exceptions import DayliLogAuthorizationError


class UserNotProjectMemberError(DayliLogAuthorizationError):
    """Ошибка авторизации: пользователь не является участником проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция доступна только участнику проекта."):
        super().__init__(message)

class UserNotDailyLogCreator(DayliLogAuthorizationError):
    """Ошибка авторизации: пользователь не является автором записи дня."""

    def __init__(self, message: str = "Недостаточно прав: операция доступна только автору записи дня."):
        super().__init__(message)


class UserNotProjectAdminError(DayliLogAuthorizationError):
    """Ошибка авторизации: пользователь не является администратором проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция доступна только администратору проекта."):
        super().__init__(message)