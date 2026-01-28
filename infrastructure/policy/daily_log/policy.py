from application.daily_log import interfaces
from application.daily_log.exceptions import DayliLogAuthorizationError
from domain import entities
import exceptions


class DailyLogAuthorizationPolicy(interfaces.DailyLogAuthorizationPolicy):

    def decide_create_daily_log(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> DayliLogAuthorizationError | None:
        error = actor.decide_create_daily_log(project, project_members)

        if error is entities.UserDecisions.CreateDailyLogDecision.FORBIDDEN_FOR_NON_MEMBER:
            raise exceptions.UserNotProjectMemberError('Пользователь не является участником проекта')


    def decide_update_daily_log(self, actor: entities.User, daily_log: entities.DailyLog) -> DayliLogAuthorizationError | None:
        error = actor.decide_update_daily_log(daily_log)

        if error is entities.UserDecisions.UpdateDailyLogDecision.FORBIDDEN_FOR_NON_CREATOR:
            raise exceptions.UserNotDailyLogCreator('Пользователю не принадлежит целевая запись дня')
        
    def decide_get_daily_log(self, actor: entities.User, daily_log: entities.DailyLog, project_members: list[entities.User]) -> DayliLogAuthorizationError | None:
        error = actor.decide_get_daily_log(daily_log, project_members)
        
        if error is entities.UserDecisions.GetDailyLogDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR:
            raise exceptions.UserNotProjectAdminError('Пользователь не является админом проекта')

    def decide_get_daily_log_list(self, actor: entities.User, target: entities.User, project: entities.Project, project_members: list[entities.User]) -> DayliLogAuthorizationError | None:
        error = actor.decide_get_daily_log_list(target, project, project_members)

        if error is entities.UserDecisions.DecideGetDailyLogListDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR:
            raise exceptions.UserNotProjectAdminError('Пользователь не является администратором проекта и не может получить дневник активности целевого пользователя.')
        
