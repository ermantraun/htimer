class SubscriptionAuthorizationError(Exception):
    """Ошибка авторизации подписки (subscription)."""
    pass


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


class PaymentAuthorizationError(Exception):
    """Raised when there is an authorization error related to payments."""
    pass


class CantCreatePayment(Exception):
    """Raised when a payment cannot be created due to business rules (ensure_create)."""
    pass

class CantCompletePayment(Exception):
    """Raised when a payment cannot be completed due to business rules."""
    pass
