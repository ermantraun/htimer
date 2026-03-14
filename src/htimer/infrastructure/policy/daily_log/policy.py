from htimer.application.daily_log import interfaces
from htimer.application.daily_log.exceptions import DayliLogAuthorizationError
from htimer.domain import entities

from . import exceptions


class DailyLogAuthorizationPolicy(interfaces.DailyLogAuthorizationPolicy):
    def decide_create_daily_log(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
    ) -> DayliLogAuthorizationError | None:
        error = actor.decide_create_daily_log(project, project_members)

        if (
            error
            is entities.UserDecisions.CreateDailyLogDecision.FORBIDDEN_FOR_NON_MEMBER
        ):
            raise exceptions.UserNotProjectMemberError(
                "Недостаточно прав: создание записи дня доступно только участнику проекта."
            )

    def decide_update_daily_log(
        self, actor: entities.User, daily_log: entities.DailyLog
    ) -> DayliLogAuthorizationError | None:
        error = actor.decide_update_daily_log(daily_log)

        if (
            error
            is entities.UserDecisions.UpdateDailyLogDecision.FORBIDDEN_FOR_NON_CREATOR
        ):
            raise exceptions.UserNotDailyLogCreator(
                "Недостаточно прав: изменение записи дня доступно только её автору."
            )

    def decide_get_daily_log(
        self,
        actor: entities.User,
        daily_log: entities.DailyLog,
        project_members: list[entities.User],
    ) -> DayliLogAuthorizationError | None:
        error = actor.decide_get_daily_log(daily_log, project_members)

        if (
            error
            is entities.UserDecisions.GetDailyLogDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR
        ):
            raise exceptions.UserNotProjectAdminError(
                "Недостаточно прав: просмотр записи дня доступен только администратору проекта или автору записи."
            )

    def decide_get_daily_log_list(
        self,
        actor: entities.User,
        target: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
    ) -> DayliLogAuthorizationError | None:
        error = actor.decide_get_daily_log_list(target, project, project_members)

        if (
            error
            is entities.UserDecisions.DecideGetDailyLogListDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR
        ):
            raise exceptions.UserNotProjectAdminError(
                "Недостаточно прав: просмотр списка записей другого пользователя доступен только администратору проекта или автору."
            )
