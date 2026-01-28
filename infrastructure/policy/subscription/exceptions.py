from application.subscription.exceptions import SubscriptionAuthorizationError

class UserNotProjectCreatorError(SubscriptionAuthorizationError):
    """Raised when the user is not an admin and attempted an admin-only subscription operation."""
    pass
