from application.project.exceptions import ProjectAuthorizationError


class UserNotAdminError(ProjectAuthorizationError):
    """Ошибка: пользователь не является администратором."""
    pass


class ProjectBlockedError(ProjectAuthorizationError):
    """Ошибка: проект неактивен."""
    pass

class UserNotCreatorError(ProjectAuthorizationError):
    """Ошибка: пользователь не является создателем проекта."""
    pass

class UserNotProjectAdminError(ProjectAuthorizationError):
    """Ошибка: пользователь не является администратором проекта."""
    pass

class UserNotProjectMemberError(ProjectAuthorizationError):
    """Ошибка: пользователь не является участником проекта."""
    pass