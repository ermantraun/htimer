from uuid import uuid4
from domain import entities
from application.common_interfaces import DBSession
from . import interfaces
from . import validators
from . import dto
from . import exceptions
from . import policy


class CreateUserInteractor:
    def __init__(
        self,
        session: DBSession,
        context: interfaces.UserContext,
        user_getter: interfaces.UserGetter,
        hash_generator: interfaces.HashGenerator,
        user_creator: interfaces.UserCreator,
        validator: validators.CreateUserValidator,
        user_policy: policy.UserPolicy,
    ):
        self.user_getter = user_getter
        self.user_creator = user_creator
        self.validator = validator
        self.context = context
        self.hash_generator = hash_generator
        self.session = session
        self.policy = user_policy
        
    async def execute(self, data: dto.CreateUserInDTO) -> dto.CreateUserOutDTO:
        # Get current user
        current_user_uuid = self.context.get_current_user_uuid()
        if isinstance(current_user_uuid, exceptions.InvalidToken):
            raise current_user_uuid

        current_user = await self.user_getter.get(current_user_uuid)
        if isinstance(current_user, exceptions.UserRepositoryError):
            raise current_user

        # Check authorization first
        auth_error = self.policy.can_create_user(current_user)
        if auth_error is not None:
            raise auth_error

        # Then validate data
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        # Create user
        password_hash = self.hash_generator.generate(data.password)
        
        new_user = entities.User(
            uuid=uuid4(),
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            creator_uuid=current_user.uuid,
            is_active=data.is_active if data.is_active is not None else True,
            is_archived=data.is_archived if data.is_archived is not None else False,
            is_admin=data.is_admin
        )
        created_user = await self.user_creator.create(new_user)

        if isinstance(created_user, exceptions.UserRepositoryError):
            raise created_user

        await self.session.commit()
        
        return dto.CreateUserOutDTO(
            name=created_user.name,
            email=created_user.email,
            is_active=created_user.is_active,
            is_archived=created_user.is_archived,
            is_admin=created_user.is_admin
        )
    
    
class UpdateUserInteractor:
    def __init__(
        self,
        session: DBSession,
        user_updater: interfaces.UserUpdater,
        user_projects_getter: interfaces.UserProjectsGetter,
        user_getter: interfaces.UserGetter,
        context: interfaces.UserContext,
        validator: validators.UpdateUserValidator,
        user_policy: policy.UserPolicy,
    ):
        self.user_context = context
        self.validator = validator
        self.user_updater = user_updater
        self.user_getter = user_getter
        self.user_projects_getter = user_projects_getter
        self.session = session
        self.policy = user_policy
        
    async def execute(self, data: dto.UpdateUserInDTO) -> dto.UpdateUserOutDTO:
        # Get current user (actor)
        actor_uuid = self.user_context.get_current_user_uuid()
        if isinstance(actor_uuid, exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_getter.get(actor_uuid)
        if isinstance(actor, exceptions.UserRepositoryError):
            raise actor

        # Determine target user
        if data.uuid is not None:
            # Remote update - updating another user
            target = await self.user_getter.get(data.uuid)
            if isinstance(target, exceptions.UserRepositoryError):
                raise target
            
            # Get projects for authorization check
            actor_projects = await self.user_projects_getter.get(actor.uuid)
            if isinstance(actor_projects, exceptions.UserRepositoryError):
                raise actor_projects
            
            target_projects = await self.user_projects_getter.get(target.uuid)
            if isinstance(target_projects, exceptions.UserRepositoryError):
                raise target_projects
            
            # Check authorization
            auth_error = self.policy.can_update_user(
                actor=actor,
                target=target,
                update_data=data,
                actor_projects=actor_projects,
                target_projects=target_projects,
            )
            if auth_error is not None:
                raise auth_error
        else:
            # Self update
            target = actor
            
            # Check authorization
            auth_error = self.policy.can_update_user(
                actor=actor,
                target=target,
                update_data=data,
            )
            if auth_error is not None:
                raise auth_error
        
        # Validate data
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error
    
        # Update user
        updated_user = await self.user_updater.update(data)
        if isinstance(updated_user, exceptions.UserRepositoryError):
            raise updated_user
        
        await self.session.commit()
        
        return dto.UpdateUserOutDTO(
            name=updated_user.name,
            email=updated_user.email,
            is_active=updated_user.is_active,
            is_archived=updated_user.is_archived,
            is_admin=updated_user.is_admin
        )




class GetUsersInteractor:
    def __init__(
        self,
        user_getter: interfaces.UserGetter,
        context: interfaces.UserContext,
        user_projects_getter: interfaces.UserProjectsGetter,
        projects_users_getter: interfaces.ProjectsUsersGetter,
        validator: validators.GetUsersListValidator,
        user_policy: policy.UserPolicy,
    ):
        self.user_getter = user_getter
        self.user_context = context
        self.user_projects_getter = user_projects_getter
        self.projects_users_getter = projects_users_getter
        self.validator = validator
        self.policy = user_policy
        
    async def execute(self, data: dto.GetUsersInDto) -> list[dto.UpdateUserOutDTO]:
        # Get current user
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, exceptions.InvalidToken):
            raise current_user_uuid
        
        current_user = await self.user_getter.get(current_user_uuid)
        if isinstance(current_user, exceptions.UserRepositoryError):
            raise current_user
        
        # Get user's projects
        user_projects = await self.user_projects_getter.get(current_user_uuid)
        if isinstance(user_projects, exceptions.UserRepositoryError):
            raise user_projects
        
        user_projects_names = {p.name for p in user_projects}
        
        # Check authorization
        auth_error = self.policy.can_list_users(
            actor=current_user,
            filter_data=data,
            actor_projects_names=user_projects_names,
        )
        if auth_error is not None:
            raise auth_error
        
        # Validate data
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error
        
        # Get users
        projects_uuid = [
            project.uuid 
            for project in user_projects 
            if project.name in data.projects_names
        ] if data.projects_names else None
        
        users = await self.projects_users_getter.get(
            projects_uuid=projects_uuid,
            is_active=data.status
        )
        
        if isinstance(users, exceptions.UserRepositoryError):
            raise users
        
        return [
            dto.UpdateUserOutDTO(
                name=user.name,
                email=user.email,
                is_active=user.is_active,
                is_archived=user.is_archived,
                is_admin=user.is_admin
            ) for user in users
        ]


