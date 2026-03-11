from htimer.application.subscription.exceptions import SubscriptionAuthorizationError


class UserNotProjectCreatorError(SubscriptionAuthorizationError):
    """Ошибка авторизации: пользователь не является создателем проекта."""

    def __init__(self, message: str = "Недостаточно прав: операция с подпиской доступна только создателю проекта."):
        super().__init__(message)
