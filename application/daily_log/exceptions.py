class DayliLogAuthorizationError(Exception):
    """Raised when there is an authorization error related to daily logs."""
    pass


class DayliLogValidationError(Exception):
    """Базовое исключение валидации для записей дня."""
    pass


class InvalidDailyLogDescriptionError(DayliLogValidationError):
    """Raised when provided description is invalid (too long)."""
    pass