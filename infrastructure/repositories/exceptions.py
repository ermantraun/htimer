class InvalidToken(Exception):
	"""Raised when a token is invalid."""


class RepositoryError(Exception):
	"""Raised when there is a generic repository error."""


class UserRepositoryError(RepositoryError):
	"""Raised when there is an error in the user repository."""


class EmailAlreadyExistsError(UserRepositoryError):
	"""Raised when a user with the same email already exists."""


class UserNotFoundError(UserRepositoryError):
	"""Raised when a user is not found."""


class ProjectRepositoryError(RepositoryError):
	"""Raised when there is an error in the project repository."""


class UserAlreadyHasProjectError(ProjectRepositoryError):
	"""Raised when a user already has a project with the same name."""


class ProjectNotFoundError(ProjectRepositoryError):
	"""Raised when a project is not found."""


class MemberNotFound(ProjectRepositoryError):
	"""Raised when a user is not in the project members."""


class UserAlreadyProjectMemberError(ProjectRepositoryError):
	"""Raised when a user is already a project member."""


class StageRepositoryError(RepositoryError):
	"""Raised when there is an error in the stage repository."""


class StageNotFoundError(StageRepositoryError):
	"""Raised when a stage is not found."""


class StageAlreadyExistsError(StageRepositoryError):
	"""Raised when a stage already exists."""


class ParentStageAlreadyHasMainSubStageError(StageRepositoryError):
	"""Raised when a parent stage already has a main sub-stage."""


class DailyLogRepositoryError(RepositoryError):
	"""Raised when there is an error in the daily log repository."""


class DailyLogAlreadyExistsError(DailyLogRepositoryError):
	"""Raised when a daily log already exists for the given criteria."""


class DailyLogNotFoundError(DailyLogRepositoryError):
	"""Raised when a daily log is not found."""


class TaskRepositoryError(RepositoryError):
	"""Raised when there is an error in the task repository."""


class TaskNotFoundError(TaskRepositoryError):
	"""Raised when a task is not found."""


class TaskAlreadyExistsError(TaskRepositoryError):
	"""Raised when a task already exists."""


class InvalidDate(Exception):
	"""Raised when a provided date is invalid."""


class PaymentRepositoryError(RepositoryError):
	"""Raised when there is an error in the payment repository."""


class PaymentNotFoundError(PaymentRepositoryError):
	"""Raised when a payment is not found."""


class SubscriptionRepositoryError(RepositoryError):
	"""Raised when there is an error in the subscription repository."""


class SubscriptionNotFoundError(SubscriptionRepositoryError):
	"""Raised when a subscription is not found."""


class SubscriptionAlreadyExistsError(SubscriptionRepositoryError):
	"""Raised when a subscription already exists."""


class PaymentGatewayError(Exception):
	"""Raised when there is an error with the payment gateway."""


class PaymentFailedError(PaymentGatewayError):
	"""Raised when a payment through the gateway fails."""


class PaymentNotComplete(PaymentGatewayError):
	"""Raised when a payment is not completed successfully."""


class PaymentNotExistsError(PaymentGatewayError):
	"""Raised when a payment does not exist."""


class PaymentRefundFailedError(PaymentGatewayError):
	"""Raised when a payment refund fails."""


class FileRepositoryError(RepositoryError):
	"""Raised when there is an error in the file repository."""


class FileAlreadyExistsError(FileRepositoryError):
	"""Raised when a file already exists."""


class FileNotFoundError(FileRepositoryError):
	"""Raised when a file is not found."""