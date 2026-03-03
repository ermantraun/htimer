from application.reports import exceptions


class UserNotProjectAdmin(exceptions.ReportAuthorizationError):
    pass

class TargetUsersNotProjectMembers(exceptions.ReportAuthorizationError):
    pass
