from application.task import interfaces
from domain import entities
import infrastructure.policy.task.exceptions as exceptions


class TaskAuthorizationPolicyImpl(interfaces.TaskAuthorizationPolicy):
    def decide_create_task(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_create_task(project, project_members)

        if decision is entities.UserDecisions.CreateTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.CreateTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Пользователь не является участником проекта и не может создать задачу.")

        return None

    def decide_update_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_update_task(task, project_members)

        if decision is entities.UserDecisions.UpdateTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.UpdateTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Пользователь не имеет прав обновлять задачу.")

        return None

    def decide_get_task(self, actor: entities.User, task_project: entities.Project,task_project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        
        decision = actor.decide_get_task(task_project, task_project_members)

        if decision is entities.UserDecisions.GetTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.GetTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Пользователь не является участником проекта и не может получить задачу.")

        return None

    def decide_delete_task(self, actor: entities.User, task: entities.Task, project_members: list[entities.User]) -> exceptions.UserNotProjectMemberError | None:
        decision = actor.decide_delete_task(task, project_members)

        if decision is entities.UserDecisions.DeleteTaskDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.DeleteTaskDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError("Пользователь не имеет прав удалять задачу.")

        return None
