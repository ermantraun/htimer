from htimer.domain import entities
from htimer.application.project import interfaces
import htimer.infrastructure.policy.project.project_exceptions as project_exceptions

class ProjectAuthorizationPolicyImpl(interfaces.ProjectAuthorizationPolicy):

    def decide_create_project(self, actor: entities.User) -> project_exceptions.UserNotAdminError | None:
        error = actor.decide_create_project()

        if error is entities.UserDecisions.CreateProjectDecision.ALLOWED:
            return None

        if error is entities.UserDecisions.CreateProjectDecision.FORBIDDEN_FOR_NON_ADMIN:
            return project_exceptions.UserNotAdminError(
                "Недостаточно прав: создание проекта доступно только администратору."
            )

        return None
    
    def decide_update_project(self, actor: entities.User, project: entities.Project, members: list[entities.User]) -> project_exceptions.UserNotProjectAdminError | None:
        error = actor.decide_update_project(project, members)

        if error is entities.UserDecisions.UpdateProjectDecision.ALLOWED:
            return None

        if error is entities.UserDecisions.UpdateProjectDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN_OR_CREATOR:
            return project_exceptions.UserNotProjectAdminError(
                "Недостаточно прав: обновление проекта доступно только администратору проекта."
            )


        return None
    
    
    def decide_get_project(self, actor: entities.User, project: entities.Project, members: list[entities.User]) -> project_exceptions.UserNotProjectMemberError | None:
        error = actor.decide_get_project(project, members)

        if error is entities.UserDecisions.GetProjectDecision.ALLOWED:
            return None

        if error is entities.UserDecisions.GetProjectDecision.FORBIDDEN_FOR_NON_MEMBER:
            return project_exceptions.UserNotProjectMemberError(
                "Недостаточно прав: просмотр проекта доступен только участнику проекта."
            )

        return None
