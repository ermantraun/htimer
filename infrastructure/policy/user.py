
from domain import entities
from application.user import dto, exceptions


class UserAuthorizationPolicyImpl:
    
    def can_create_user(self, actor: entities.User) -> exceptions.UserValidationError | None:
        if not actor.can_create_users():
            return exceptions.UserCannotCreateUsersError(
                "Пользователь не имеет прав для создания других пользователей."
            )
        return None
    
    def can_update_user(
        self,
        actor: entities.User,
        target: entities.User,
        update_data: dto.UpdateUserInDTO,
        actor_projects: set[entities.Project] | None = None,
        target_projects: set[entities.Project] | None = None,
    ) -> exceptions.UserValidationError | None:
        decision = actor.decide_update_user(
            target,
            change_admin=update_data.is_admin is not None,
            change_status=(update_data.is_active is not None or update_data.is_archived is not None),
            target_projects_names={p.name for p in target_projects} if target_projects is not None else None,
            actor_projects_names={p.name for p in actor_projects} if actor_projects is not None else None,
        )

        if decision is entities.UpdateUserDecision.ALLOWED:
            return None

        if decision is entities.UpdateUserDecision.SELF_ADMIN_CHANGE_FORBIDDEN:
            return exceptions.CannotChangeAdminSelfError(
                "Нельзя изменять права администратора самому себе."
            )

        if decision is entities.UpdateUserDecision.SELF_STATUS_CHANGE_FORBIDDEN:
            return exceptions.CannotChangeStatusSelfError(
                "Нельзя менять статус активности или архивности своего аккаунта."
            )

        if decision in {
            entities.UpdateUserDecision.PROJECT_CONTEXT_MISSING,
            entities.UpdateUserDecision.TARGET_PROJECT_NOT_OWNED,
        }:
            return exceptions.AdminIsNotProjectOwner(
                "Пользователь не имеет прав для изменения других пользователей."
            )

        return None
    
    def can_list_users(
        self,
        actor: entities.User,
        filter_data: dto.GetUsersInDto,
        actor_projects_names: set[str],
    ) -> exceptions.UserValidationError | None:
        decision = actor.decide_list_users(
            requested_projects_names=set(filter_data.projects_names) if filter_data.projects_names is not None else None,
            actor_projects_names=actor_projects_names,
        )

        if decision is entities.ListUsersDecision.ALLOWED:
            return None

        if decision is entities.ListUsersDecision.NOT_ADMIN:
            return exceptions.UserIsNotAdmin(
                "Только администратор может получать список пользователей."
            )

        if decision is entities.ListUsersDecision.PROJECT_ACCESS_DENIED:
            return exceptions.AdminIsNotProjectOwner(
                "Запрошены проекты, к которым у пользователя нет доступа."
            )

        return None
