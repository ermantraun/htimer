from htimer.application.reports import exceptions


class UserNotProjectAdmin(exceptions.ReportAuthorizationError):
    """Ошибка авторизации: пользователь не является администратором проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция с отчётом доступна только администратору проекта."):
        super().__init__(message)

class TargetUsersNotProjectMembers(exceptions.ReportAuthorizationError):
    """Ошибка авторизации: среди целевых пользователей есть неучастники проекта."""

    def __init__(self, message: str = "Недостаточно прав: нельзя выполнять операцию для пользователей, не входящих в проект."):
        super().__init__(message)
