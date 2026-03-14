from htimer.application.reports import interfaces
from htimer.domain import entities

from . import exceptions


class ReportsAuthorizationPolicyImpl(interfaces.ReportsAuthorizationPolicy):
    def decide_create_report(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
        target_users: list[entities.User] | None,
    ) -> (
        exceptions.UserNotProjectAdmin | exceptions.TargetUsersNotProjectMembers | None
    ):
        decision = actor.decide_create_report(project, project_members, target_users)

        if decision is entities.UserDecisions.CreateReportDecision.ALLOWED:
            return None

        if (
            decision
            is entities.UserDecisions.CreateReportDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN
        ):
            return exceptions.UserNotProjectAdmin(
                "Недостаточно прав: формирование отчёта доступно только администратору проекта или для собственных данных."
            )

        if (
            decision
            is entities.UserDecisions.CreateReportDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_AND_NON_TARGET
        ):
            return exceptions.UserNotProjectAdmin(
                "Недостаточно прав: формирование отчёта доступно только администратору проекта или для собственных данных."
            )

        if (
            decision
            is entities.UserDecisions.CreateReportDecision.FORBIDDEN_GET_NON_PROJECT_USERS
        ):
            return exceptions.TargetUsersNotProjectMembers(
                "Недостаточно прав: нельзя формировать отчёт для пользователей, не являющихся участниками проекта."
            )

        return None
