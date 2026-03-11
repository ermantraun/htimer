from htimer.application import common_exceptions


class SubscriptionAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с подпиской."""

    def __init__(self, message: str = "Недостаточно прав для операции с подпиской."):
        super().__init__(message)


class CantCreateSubscription(Exception):
    """Raised when a subscription cannot be created due to business rules (ensure_create)."""
    pass


class CantUpdateSubscription(Exception):
    """Raised when a subscription cannot be updated (e.g., cancelled) due to business rules."""
    pass

class CantActivateSubscription(Exception):
    """Raised when a subscription cannot be activated due to business rules."""
    pass

class CantExtendSubscription(Exception):
    """Raised when a subscription cannot be extended due to business rules."""
    pass


class PaymentAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с платежом."""

    def __init__(self, message: str = "Недостаточно прав для операции с платежом."):
        super().__init__(message)


class CantCreatePayment(Exception):
    """Raised when a payment cannot be created due to business rules (ensure_create)."""
    pass

class CantCompletePayment(Exception):
    """Raised when a payment cannot be completed due to business rules."""
    pass
