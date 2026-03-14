from htimer.application import common_exceptions


class DayliLogAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с записями дня."""

    def __init__(self, message: str = "Недостаточно прав для операции с записью дня."):
        super().__init__(message)


class DayliLogValidationError(Exception):
    """Базовое исключение валидации для записей дня."""

    pass


class InvalidDailyLogDescriptionError(DayliLogValidationError):
    """Raised when provided description is invalid (too long)."""

    pass
