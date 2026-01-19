from domain import entities
from application.user import interfaces
import infrastructure.policy.user.user_exceptions as user_exceptions

class UserAuthorizationPolicyImpl(interfaces.UserCreateAuthorizationPolicy,
                                  interfaces.UserUpdateAuthorizationPolicy,
                                  interfaces.UsersListAuthorizationPolicy,
                                  interfaces.UserPasswordResetAuthorizationPolicy):

    def decide_create_user(self, actor: entities.User) -> user_exceptions.UserAuthorizationError | None:
        decision = actor.decide_create_users()

        if decision is entities.UserDecisions.CreateUserDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.CreateUserDecision.FORBIDDEN_FOR_NON_ADMIN:
            return user_exceptions.UserCannotCreateUsersError(
                "Пользователь не имеет прав на создание других пользователей."
            )

        return None

    def decide_update_user(
        self,
        actor: entities.User,
        target: entities.User,
    ) -> user_exceptions.UserAuthorizationError | None:
        decision = actor.decide_update_user(
            target,

        )

        if decision is entities.UserDecisions.UpdateUserDecision.ALLOWED:
            return None


        if decision in {
            entities.UserDecisions.UpdateUserDecision.FORBIDDEN_FOR_NON_CREATOR,
        }:
            return user_exceptions.UserCannotUpdateUserError(
                "Пользователь не имеет прав для изменения целевого пользователя."
            )

        return None

    def decide_get_users_list(
        self,
        actor: entities.User,
        projects_names: set[str],
        actor_projects_names: set[str],
    ) -> user_exceptions.AdminIsNotProjectOwner | None:
        decision = actor.decide_get_users(
            requested_projects_names=set(projects_names),
            actor_projects_names=actor_projects_names,
        )

        if decision is entities.UserDecisions.ListUsersDecision.ALLOWED:
            return None

        if decision is entities.UserDecisions.ListUsersDecision.FORBIDDEN_FOR_NON_PROJECT_ADMIN:
            return user_exceptions.AdminIsNotProjectOwner(
                "Запрошены проекты, к которым у пользователя нет доступа."
            )

        return None
    
    def decide_reset_user_password(
        self,
        actor: entities.User,
        target: entities.User,
    ) -> user_exceptions.UserAuthorizationError | None:
        decision = actor.decide_reset_user_password(
            target,
        )

        if decision is entities.UserDecisions.ResetUserPasswordDecision.ALLOWED:
            return None


        if decision is entities.UserDecisions.ResetUserPasswordDecision.FORBIDDEN_FOR_NON_CREATOR:
            return user_exceptions.UserCannotResetPasswordError(
                "Пользователь не имеет прав для сброса пароля целевому пользователю."
            )
            
        return None