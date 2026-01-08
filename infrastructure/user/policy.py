"""
User authorization policy implementation.

This infrastructure layer implements authorization decisions based on domain rules.
"""
from domain import entities
from application.user import dto, exceptions


class UserAuthorizationPolicyImpl:
    """Implementation of user authorization policy."""
    
    def can_create_user(self, actor: entities.User) -> exceptions.UserValidationError | None:
        """Check if actor can create users."""
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
        """
        Check if actor can update target user with given data.
        
        Rules:
        - Users can update their own profile (name, email, password)
        - Users cannot change their own admin/active/archived status
        - Admins can update users in projects they manage
        - Admin status changes require admin performing remote update
        """
        is_self_update = actor.uuid == target.uuid
        
        # Self-update: allowed but with restrictions
        if is_self_update:
            # Cannot change own admin status
            if update_data.is_admin is not None:
                return exceptions.CannotChangeAdminSelfError(
                    "Нельзя изменять права администратора самому себе."
                )
            
            # Cannot change own active/archived status
            if update_data.is_active is not None or update_data.is_archived is not None:
                return exceptions.CannotChangeStatusSelfError(
                    "Нельзя менять статус активности или архивности своего аккаунта."
                )
            
            return None
        
        # Remote update: check if actor has permission
        if actor_projects is None or target_projects is None:
            # Projects not provided, can't determine permission
            return exceptions.AdminIsNotProjectOwner(
                "Не удалось проверить права доступа к проектам пользователя."
            )
        
        actor_project_names = {p.name for p in actor_projects}
        target_project_names = {p.name for p in target_projects}
        
        if not actor.can_update_users(
            user_projects_names=target_project_names,
            admin_projects_names=actor_project_names
        ):
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
        """
        Check if actor can list users with given filters.
        
        Rules:
        - Only admins can list users
        - Can only request users from projects actor has access to
        """
        if not actor.is_admin:
            return exceptions.UserIsNotAdmin(
                "Только администратор может получать список пользователей."
            )
        
        if filter_data.projects_names is not None:
            requested_projects = set(filter_data.projects_names)
            # Check if actor has access to all requested projects
            if not actor_projects_names <= requested_projects:
                return exceptions.AdminIsNotProjectOwner(
                    "Запрошены проекты, к которым у пользователя нет доступа."
                )
        
        return None
