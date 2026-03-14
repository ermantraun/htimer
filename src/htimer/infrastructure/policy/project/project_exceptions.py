from htimer.application.project.exceptions import ProjectAuthorizationError


class UserNotAdminError(ProjectAuthorizationError):
    """Ошибка авторизации: пользователь не является администратором."""

    def __init__(
        self,
        message: str = "Недостаточно прав: операция доступна только администратору.",
    ):
        super().__init__(message)


class ProjectBlockedError(ProjectAuthorizationError):
    """Ошибка авторизации: проект неактивен для выполнения операции."""

    def __init__(
        self,
        message: str = "Недостаточно прав: операция недоступна для неактивного проекта.",
    ):
        super().__init__(message)


class UserNotCreatorError(ProjectAuthorizationError):
    """Ошибка авторизации: пользователь не является создателем проекта."""

    def __init__(
        self,
        message: str = "Недостаточно прав: операция доступна только создателю проекта.",
    ):
        super().__init__(message)


class UserNotProjectAdminError(ProjectAuthorizationError):
    """Ошибка авторизации: пользователь не является администратором проекта."""

    def __init__(
        self,
        message: str = "Недостаточно прав: операция доступна только администратору проекта.",
    ):
        super().__init__(message)


class UserNotProjectMemberError(ProjectAuthorizationError):
    """Ошибка авторизации: пользователь не является участником проекта."""

    def __init__(
        self,
        message: str = "Недостаточно прав: операция доступна только участнику проекта.",
    ):
        super().__init__(message)
