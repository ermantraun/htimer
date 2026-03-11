from htimer.application.task import interfaces
from htimer.domain import entities
import infrastructure.policy.task.exceptions as exceptions


class TaskAuthorizationPolicyImpl(interfaces.TaskAuthorizationPolicy):
    def decide_create_task(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_create_task(project, project_members)

        if decision is entities.UserDecisions.CreateTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.CreateTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Недостаточно прав: пользователь не является участником проекта.")

        return None

    def decide_update_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_update_task(task, project_members)

        if decision is entities.UserDecisions.UpdateTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.UpdateTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Недостаточно прав: обновление задачи доступно только участнику проекта.")

        return None

    def decide_get_task(self, actor: entities.User, task_project: entities.Project,task_project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        
        decision = actor.decide_get_task(task_project, task_project_members)

        if decision is entities.UserDecisions.GetTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.GetTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Недостаточно прав: просмотр задачи доступен только участнику проекта.")

        return None

    def decide_delete_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_delete_task(task, project_members)

        if decision is entities.UserDecisions.DeleteTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.DeleteTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Недостаточно прав: удаление задачи доступно только участнику проекта.")

        return None
