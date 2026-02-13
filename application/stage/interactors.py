from uuid import uuid4
from typing import Any
import dto, interfaces, exceptions, validators
from application import common_interfaces, common_exceptions
from domain import entities

class CreateStageInteractor:
    def __init__(
        self,
        stage_repository: common_interfaces.StageRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        subscription_repository: common_interfaces.SubscriptionRepository,
        authorization_policy: interfaces.StageAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        text_normalizer: common_interfaces.TextNormalizer,
        validator: validators.CreateStageValidator,
        
    ):
        self.stage_repository = stage_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.clock = clock
        self.validator = validator
        self.text_normalizer = text_normalizer
        
    async def execute(self, data: dto.CreateStageInDTO) -> dto.CreateStageOutDTO | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | exceptions.StageAuthorizationError | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | exceptions.InvalidStageDescriptionError | exceptions.InvalidStageNameError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        
        data.description = self.text_normalizer.normalize(data.description) if data.description else data.description
        
        validation_error = self.validator.validate(data)
        
        if validation_error is not None:
            raise validation_error
        
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project
        
        parent_stage = await self.stage_repository.get_by_uuid(data.parent_uuid) if data.parent_uuid else None
        
        if isinstance(parent_stage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise parent_stage
        
        project_members = await self.project_repository.get_members([project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members
        
        authorization_error = self.authorization_policy.decide_create_stage(actor, project, project_members)
        if authorization_error is not None:
            raise authorization_error

        
        new_stage = entities.Stage(
            uuid=uuid4(),
            name=data.name,
            description=data.description,
            creator=actor,
            project=project,
            created_at=self.clock.now_date(),
            main_path=data.main_path,
            parent=parent_stage,
            status=entities.StageStatus.ACTIVE,
        )
        
        subscription = await self.project_repository.get_current_subscription(project.uuid)
        if isinstance(subscription, common_exceptions.ProjectNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.SubscriptionNotFoundError):
            subscription = None
        if isinstance(subscription, common_exceptions.RepositoryError):
            raise subscription

        if error := new_stage.ensure_create(subscription):
            raise exceptions.StageCantCreateError(str(error))

        created_stage = await self.stage_repository.create(new_stage)
        
        if isinstance(created_stage, (common_exceptions.StageAlreadyExistsError, common_exceptions.ParentStageAlreadyHasMainSubStageError, common_exceptions.UserNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise created_stage
        
        await self.db_session.commit()
        
        return dto.CreateStageOutDTO(stage=created_stage)

class UpdateStageInteractor:
    def __init__(self,
        stage_repository: common_interfaces.StageRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        subscription_repository: common_interfaces.SubscriptionRepository,
        authorization_policy: interfaces.StageAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        validator: validators.UpdateStageValidator,
        text_normalizer: common_interfaces.TextNormalizer,
    ):
        self.stage_repository = stage_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.clock = clock
        self.validator = validator
        self.text_normalizer = text_normalizer
        
    async def execute(self, data: dto.UpdateStageInDTO) -> dto.UpdateStageOutDTO | common_exceptions.StageNotFoundError | exceptions.StageAuthorizationError | common_exceptions.UserNotFoundError | exceptions.InvalidStageNameError | exceptions.InvalidStageDescriptionError | exceptions.AllFieldsNoneError | common_exceptions.InvalidToken | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        
        if data.description is not None:
            data.description = self.text_normalizer.normalize(data.description)
        
        validation_error = self.validator.validate(data)
        
        if validation_error is not None:
            raise validation_error
        
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor
        
        stage = await self.stage_repository.get_by_uuid(data.uuid)
        if isinstance(stage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise stage
        
        project_members = await self.project_repository.get_members([stage.project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members
        
        authorization_error = self.authorization_policy.decide_update_stage(actor, stage.project, project_members)
        if authorization_error is not None:
            raise authorization_error
        
        update_data: dict[str, Any] = {}
        
        if data.name is not None:
            update_data['name'] = data.name
        if data.description is not None:
            update_data['description'] = data.description
        if data.status is not None:
            update_data['status'] = data.status
        
        subscription = await self.project_repository.get_current_subscription(stage.project.uuid)
        if isinstance(subscription, common_exceptions.ProjectNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.SubscriptionNotFoundError):
            subscription = None
        if isinstance(subscription, common_exceptions.RepositoryError):
            raise subscription

        if error := stage.ensure_update(subscription):
            raise exceptions.StageCantUpdateError(str(error))
        
        updated_stage = await self.stage_repository.update(stage.uuid, update_data)
        
        if isinstance(updated_stage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise updated_stage
        
        await self.db_session.commit()
        
        return dto.UpdateStageOutDTO(stage=updated_stage)

class DeleteStageInteractor:
    def __init__(
        self,
        stage_repository: common_interfaces.StageRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.StageAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
    ):
        self.stage_repository = stage_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context

    async def execute(self, data: dto.DeleteStageInDTO) -> None | common_exceptions.StageNotFoundError | exceptions.StageAuthorizationError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        stage = await self.stage_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(stage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise stage

        project_members = await self.project_repository.get_members([stage.project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_update_stage(actor, stage.project, project_members)
        if authorization_error is not None:
            raise authorization_error

        delete_result = await self.stage_repository.delete(stage.uuid)
        if isinstance(delete_result, common_exceptions.RepositoryError):
            raise delete_result
        await self.db_session.commit()

        return None
    
class GetStageListInteractor:
    def __init__(
        self,
        project_repository: common_interfaces.ProjectRepository,
        stage_repository: common_interfaces.StageRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.StageAuthorizationPolicy,
        context: common_interfaces.UserContext,
    ):
        self.project_repository = project_repository
        self.stage_repository = stage_repository
        self.user_repository = user_repository
        self.context = context
        self.authorization_policy = authorization_policy

    async def execute(self, data: dto.GetStageListInDTO) -> dto.GetStageListOutDTO | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.StageAuthorizationError | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)

        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)

        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project

        members = await self.project_repository.get_members([project.uuid])

        if isinstance(members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise members

        authorization_error = self.authorization_policy.decide_get_stage_list(
            actor,
            project,
            members,
        )

        if authorization_error is not None:
            raise authorization_error

        stages = await self.stage_repository.get_list(project.uuid)

        if isinstance(stages, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise stages

        return dto.GetStageListOutDTO(stages=stages)
    
