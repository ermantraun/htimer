import htimer.infrastructure.policy.stage.exceptions as infra_exceptions
from htimer.application.stage import exceptions as stage_exceptions
from htimer.application.stage import interfaces
from htimer.domain import entities


class StageAuthorizationPolicyImpl(interfaces.StageAuthorizationPolicy):
    def decide_create_stage(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
    ) -> stage_exceptions.StageAuthorizationError | None:
        actor_decision = actor.decide_create_stage(project, project_members)

        if actor_decision is entities.UserDecisions.CreateStageDecision.ALLOWED:
            return None

        if (
            actor_decision
            is entities.UserDecisions.CreateStageDecision.FORBIDDEN_FOR_NON_MEMBER
        ):
            return infra_exceptions.UserNotProjectMemberError(
                "Недостаточно прав: создание этапа доступно только участнику проекта."
            )

        return None

    def decide_update_stage(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
    ) -> stage_exceptions.StageAuthorizationError | None:
        actor_decision = actor.decide_update_stage(project, project_members)

        if actor_decision is entities.UserDecisions.UpdateStageDecision.ALLOWED:
            return None

        if (
            actor_decision
            is entities.UserDecisions.UpdateStageDecision.FORBIDDEN_FOR_NON_MEMBER
        ):
            return infra_exceptions.UserNotProjectMemberError(
                "Недостаточно прав: обновление этапа доступно только участнику проекта."
            )

        return None

    def decide_get_stage_list(
        self,
        actor: entities.User,
        project: entities.Project,
        project_members: list[entities.User],
    ) -> stage_exceptions.StageAuthorizationError | None:
        actor_decision = actor.decide_get_project(project, project_members)

        if (
            actor_decision
            is entities.UserDecisions.GetProjectDecision.FORBIDDEN_FOR_NON_MEMBER
        ):
            return infra_exceptions.UserNotProjectMemberError(
                "Недостаточно прав: просмотр списка этапов доступен только участнику проекта."
            )

        return None
