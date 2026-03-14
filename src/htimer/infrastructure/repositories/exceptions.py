class InvalidToken(Exception):
    """Ошибка: токен недействителен."""


class RepositoryError(Exception):
    """Общая ошибка репозитория."""


class UserRepositoryError(RepositoryError):
    """Ошибка репозитория пользователей."""


class EmailAlreadyExistsError(UserRepositoryError):
    """Пользователь с таким email уже существует."""


class UserNotFoundError(UserRepositoryError):
    """Пользователь не найден."""


class ProjectRepositoryError(RepositoryError):
    """Ошибка репозитория проектов."""


class UserAlreadyHasProjectError(ProjectRepositoryError):
    """У пользователя уже есть проект с таким именем."""


class ProjectNotFoundError(ProjectRepositoryError):
    """Проект не найден."""


class MemberNotFound(ProjectRepositoryError):
    """Участник проекта не найден."""


class UserAlreadyProjectMemberError(ProjectRepositoryError):
    """Пользователь уже является участником проекта."""


class StageRepositoryError(RepositoryError):
    """Ошибка репозитория этапов."""


class StageNotFoundError(StageRepositoryError):
    """Этап не найден."""


class StageAlreadyExistsError(StageRepositoryError):
    """Этап уже существует."""


class ParentStageAlreadyHasMainSubStageError(StageRepositoryError):
    """У родительского этапа уже есть основной подэтап."""


class DailyLogRepositoryError(RepositoryError):
    """Ошибка репозитория записей дня."""


class DailyLogAlreadyExistsError(DailyLogRepositoryError):
    """Запись дня с заданными параметрами уже существует."""


class DailyLogNotFoundError(DailyLogRepositoryError):
    """Запись дня не найдена."""


class TaskRepositoryError(RepositoryError):
    """Ошибка репозитория задач."""


class TaskNotFoundError(TaskRepositoryError):
    """Задача не найдена."""


class TaskAlreadyExistsError(TaskRepositoryError):
    """Задача уже существует."""


class InvalidDate(Exception):
    """Передана некорректная дата."""


class PaymentRepositoryError(RepositoryError):
    """Ошибка репозитория платежей."""


class PaymentNotFoundError(PaymentRepositoryError):
    """Платёж не найден."""


class SubscriptionRepositoryError(RepositoryError):
    """Ошибка репозитория подписок."""


class SubscriptionNotFoundError(SubscriptionRepositoryError):
    """Подписка не найдена."""


class SubscriptionAlreadyExistsError(SubscriptionRepositoryError):
    """Подписка уже существует."""


class PaymentGatewayError(Exception):
    """Ошибка платёжного шлюза."""


class PaymentFailedError(PaymentGatewayError):
    """Ошибка выполнения платежа через шлюз."""


class PaymentNotComplete(PaymentGatewayError):
    """Платёж не завершён успешно."""


class PaymentNotExistsError(PaymentGatewayError):
    """Платёж не существует."""


class PaymentRefundFailedError(PaymentGatewayError):
    """Ошибка возврата платежа."""


class FileRepositoryError(RepositoryError):
    """Ошибка репозитория файлов."""


class FileAlreadyExistsError(FileRepositoryError):
    """Файл уже существует."""


class FileNotFoundError(FileRepositoryError):
    """Файл не найден."""


class ReportRepositoryError(RepositoryError):
    """Ошибка репозитория отчётов."""


class ReportNotFoundError(ReportRepositoryError):
    """Отчёт не найден."""
