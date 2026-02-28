
class ReportAuthorizationError(Exception):
    pass

class ValidateReportRequestError(Exception):
    pass

class InvalidPeriodError(ValidateReportRequestError):
    pass

class ReportCreateError(Exception):
    pass