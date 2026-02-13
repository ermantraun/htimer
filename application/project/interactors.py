from uuid import uuid4
from dataclasses import asdict
from application import common_exceptions, common_interfaces
from domain import entities
import exceptions, interfaces, validators, dto


def normalize_description(description: str | None) -> str | None:
    if description is None:
        return None
    desc = description.strip()
    return desc if desc != "" else None
    
    
class CreateProjectInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        create_project_validator: validators.CreateProjectValidator,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        user_context: common_interfaces.UserContext,
        user_repository : common_interfaces.UserRepository,
        clock: common_interfaces.Clock,
        text_normalizer: common_interfaces.TextNormalizer,
    ):
        self.create_project_validator = create_project_validator
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.user_context = user_context
        self.user_repository = user_repository
        self.clock = clock
        self.text_normalizer = text_normalizer
        self.project_repository = project_repository
        
    async def execute(self, data: dto.CreateProjectInDTO) -> dto.CreateProjectOutDTO | common_exceptions.UserAlreadyHasProjectError | common_exceptions.InvalidToken | exceptions.ProjectAuthorizationError | exceptions.InvalidProjectDescriptionError | exceptions.InvalidProjectNameError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        

        if data.description is not None:
            data.description = self.text_normalizer.normalize(data.description)
        
        validation_error = self.create_project_validator.validate(data)
        if validation_error is not None:
            raise validation_error
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid

        actor = await self.user_repository.get_by_uuid(current_user_uuid)
        
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise common_exceptions.InvalidToken("Current user not found")
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
        authorization_error = self.authorization_policy.decide_create_project(actor)
        if authorization_error is not None:
            raise authorization_error   


        new_project = entities.Project(
            uuid=uuid4(),
            name=data.name,
            creator=actor,
            description=data.description,
            created_at=self.clock.now_date(),
        )

        created_project = await self.project_repository.create(new_project)
        if isinstance(created_project, (common_exceptions.UserAlreadyHasProjectError, common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            return created_project

        await self.db_session.commit()

        return dto.CreateProjectOutDTO(
            project=created_project
        )
    
    
    
class UpdateProjectInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        subscription_repository: common_interfaces.SubscriptionRepository,
        update_project_validator: validators.UpdateProjectValidator,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        user_context: common_interfaces.UserContext,
        user_repository: common_interfaces.UserRepository,
        text_normalizer: common_interfaces.TextNormalizer,
    ):
        self.update_project_validator = update_project_validator
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.user_context = user_context
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.subscription_repository = subscription_repository
        self.text_normalizer = text_normalizer
        
    async def execute(self, data: dto.UpdateProjectInDTO) -> dto.UpdateProjectOutDTO | common_exceptions.SubscriptionNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.InvalidToken | exceptions.ProjectAuthorizationError | exceptions.InvalidProjectDescriptionError | exceptions.InvalidProjectNameError | common_exceptions.RepositoryError:
        

        if data.description is not None:
            data.description = self.text_normalizer.normalize(data.description)
        
        validation_error = self.update_project_validator.validate(data)
        if validation_error is not None:
            raise validation_error
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid

        actor = await self.user_repository.get_by_uuid(current_user_uuid)
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor

        project = await self.project_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(project, common_exceptions.RepositoryError):
            raise project

        members = await self.project_repository.get_members([project.uuid])
        
        if isinstance(members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise members
        
        authorization_error = self.authorization_policy.decide_update_project(
            actor,
            project, 
            members,
        )
        
        
        if authorization_error is not None:
            raise authorization_error

        subscription = await self.project_repository.get_current_subscription(project.uuid)
        if isinstance(subscription, common_exceptions.ProjectNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.SubscriptionNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.RepositoryError):
            raise subscription
        
        
        if error := project.ensure_update(subscription):
            raise exceptions.CantUpdateProjectError(error)

        updated_project = await self.project_repository.update(project.uuid, asdict(data))

        if isinstance(updated_project, (common_exceptions.ProjectNotFoundError, common_exceptions.UserAlreadyHasProjectError, common_exceptions.RepositoryError)):
            raise updated_project
        
        await self.db_session.commit()

        return dto.UpdateProjectOutDTO(
            project=updated_project
            )
        

class GetProjectInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.UserContext,
        
    ):
        self.project_repository = project_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.user_repository = user_repository
        self.context = context
        
    async def execute(self, data: dto.GetProjectInDTO) -> dto.GetProjectsOutDTO | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)

        if isinstance(project, common_exceptions.RepositoryError):
            raise project
        

        members = await self.project_repository.get_members([project.uuid]) 
        if isinstance(members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise members
        
        
        authorization_error = self.authorization_policy.decide_get_project(
            actor,
            project,
            members) # type: ignore
        
        if authorization_error is not None:
            raise authorization_error
        
        return dto.GetProjectsOutDTO(
            project=project,
            members=members)  # type: ignore


class GetProjectListInteractor:
    def __init__(
        self,
        user_repository: common_interfaces.UserRepository,
        user_context: common_interfaces.UserContext,
        validator: validators.GetProjectListValidator,
    ):
        self.user_repository = user_repository
        self.user_context = user_context
        self.validator = validator

    async def execute(self, data: dto.GetProjectListInDTO) -> dto.GetProjectListOutDTO | exceptions.ProjectValidationError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid

        projects = await self.user_repository.get_projects(current_user_uuid)
        if isinstance(projects, (common_exceptions.UserNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise projects

        return dto.GetProjectListOutDTO(projects=projects)
        
class AddMembersToProjectInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
        clock: common_interfaces.Clock,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.db_session = db_session
        self.context = context
        self.authorization_policy = authorization_policy
        self.clock = clock
    
    async def execute(self, data: dto.AddMembersInDTO) -> dto.AddMembersOutDTO | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | exceptions.ProjectAuthorizationError | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
                
        project = await self.project_repository.get_by_uuid(data.project_uuid)

        if isinstance(project, common_exceptions.RepositoryError):
            raise project
        
        project_members = await self.project_repository.get_members([project.uuid])
        
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members
        
        
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise project
        
        authorization_error = self.authorization_policy.decide_update_project(
            actor,
            project, 
            project_members,
        )
        
        
        if authorization_error is not None:
            raise authorization_error
        
        assigned_by = actor
        
        added_users = await self.user_repository.get_list(data.members_uuids)
        
        if isinstance(added_users, common_exceptions.RepositoryError):
            raise added_users
        
        members = [entities.MemberShip(
            uuid=uuid4(), 
            project=project,
            user=added_user,
            assigned_by=assigned_by,
            joined_at=self.clock.now_date()
            ) for added_user in added_users]
        
        added_members = await self.project_repository.add_members(members)
        
        if isinstance(added_members, (common_exceptions.ProjectNotFoundError, common_exceptions.UserNotFoundError, common_exceptions.UserAlreadyProjectMemberError, common_exceptions.RepositoryError)):
            raise added_members
        
        await self.db_session.commit()
        
        return dto.AddMembersOutDTO(members=added_members)


    
class RemoveMembersFromProjectInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.db_session = db_session
        self.context = context
        self.authorization_policy = authorization_policy
        
    async def execute(self, data: dto.RemoveMembersInDTO) ->  None | common_exceptions.ProjectNotFoundError | common_exceptions.MemberNotFound | exceptions.ProjectAuthorizationError | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)

        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise project

        members = await self.project_repository.get_members([project.uuid])
        
        if isinstance(members, (common_exceptions.RepositoryError, common_exceptions.ProjectNotFoundError)):
            raise members
        
        authorization_error = self.authorization_policy.decide_update_project(
            actor,
            project,
            members,
        )
        
        if authorization_error is not None:
            raise authorization_error
        
        result = await self.project_repository.remove_members(project.uuid, data.members_uuids)
        
        if isinstance(result, (common_exceptions.MemberNotFound, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise result
        
        await self.db_session.commit()
        


        
 