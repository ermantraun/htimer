from application.daily_log.exceptions import DayliLogAuthorizationError

class UserNotProjectMemberError(DayliLogAuthorizationError):
    """ Raise when user is not project member """

class UserNotDailyLogCreator(DayliLogAuthorizationError):
    """ Raise when user tried updat not his daily log """


class UserNotProjectAdminError(DayliLogAuthorizationError):
    """Raised when user is not project admin and tries to access day entries."""