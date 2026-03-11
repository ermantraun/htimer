
from htimer.application import common_exceptions


class ReportAuthorizationError(common_exceptions.AuthorizationError):
    """Ошибка авторизации при работе с отчётами."""

    def __init__(self, message: str = "Недостаточно прав для операции с отчётом."):
        super().__init__(message)

class ValidateReportRequestError(Exception):
    pass

class InvalidPeriodError(ValidateReportRequestError):
    pass

class ReportCreateError(Exception):
    pass