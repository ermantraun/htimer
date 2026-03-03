from application.user.exceptions import UserAuthorizationError

class AdminIsNotProjectOwner(UserAuthorizationError):
    """Ошибка: администратор не состоит в проекте."""
    pass

class UserIsNotAdmin(UserAuthorizationError):
    """Ошибка: пользователь не является администратором."""
    pass

class UserCannotCreateUsersError(UserAuthorizationError):
    """Ошибка: пользователь не имеет прав на создание других пользователей."""
    pass


class CannotChangeSelfError(UserAuthorizationError):
    """Попытка самим себе повысить/понизить роль/права."""
    pass


class CannotChangeStatusSelfError(UserAuthorizationError):
    """Попытка самим себе изменить активность/архивность аккаунта."""
    pass

class UserCannotUpdateUserError(UserAuthorizationError):
    """Ошибка: пользователь не имеет прав для изменения целевого пользователя."""
    pass

class CannotResetOwnPasswordError(UserAuthorizationError):
    """Ошибка: пользователь не может сбросить свой собственный пароль."""
    pass

class UserCannotResetPasswordError(UserAuthorizationError):
    """Ошибка: пользователь не имеет прав для сброса пароля целевому пользователю."""
    pass

