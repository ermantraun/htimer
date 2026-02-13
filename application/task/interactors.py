from uuid import uuid4
from application import common_exceptions, common_interfaces
from domain import entities
from typing import Any
import dto, interfaces, exceptions, validators


class CreateTaskInteractor:
    def __init__(
        self,
        task_repository: common_interfaces.TaskRepository,
        stage_repository: common_interfaces.StageRepository,
        project_repository: common_interfaces.ProjectRepository,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.TaskAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        validator: validators.CreateTaskValidator,
    ):
        self.task_repository = task_repository
        self.stage_repository = stage_repository
        self.project_repository = project_repository
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.clock = clock
        self.validator = validator

    async def execute(self, data: dto.CreateTaskInDTO) -> dto.CreateTaskOutDTO | common_exceptions.StageNotFoundError | common_exceptions.UserNotFoundError | exceptions.TaskAuthorizationError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError:
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        substage = await self.stage_repository.get_by_uuid(data.substage_uuid)
        if isinstance(substage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise substage

        project = substage.project
        project_members = await self.project_repository.get_members([project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_create_task(actor, project, project_members)
        if isinstance(authorization_error, exceptions.TaskAuthorizationError):
            raise authorization_error

        subscription = await self.project_repository.get_current_subscription(project.uuid)
        if isinstance(subscription, common_exceptions.ProjectNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.RepositoryError):
            raise subscription
        if isinstance(subscription, common_exceptions.SubscriptionNotFoundError):
            subscription = None

        ensure_err = entities.Task.ensure_create(substage, subscription)
        if ensure_err:
            raise exceptions.CantCreateTask(ensure_err)

        task = entities.Task(
            uuid=uuid4(),
            name=data.name,
            description=data.description,
            creator=actor,
            created_at=self.clock.now_date(),
            substage=substage,
        )

        created = await self.task_repository.create(task)
        if isinstance(created, (common_exceptions.TaskAlreadyExistsError, common_exceptions.RepositoryError)):
            raise created

        await self.db_session.commit()

        return dto.CreateTaskOutDTO(task=created)


class GetTaskInteractor:
    def __init__(
        self,
        task_repository: common_interfaces.TaskRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        authorization_policy: interfaces.TaskAuthorizationPolicy,
        context: common_interfaces.UserContext,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.authorization_policy = authorization_policy
        self.context = context

    async def execute(self, data: dto.GetTaskInDTO) -> dto.GetTaskOutDTO | common_exceptions.TaskNotFoundError | common_exceptions.UserNotFoundError | exceptions.TaskAuthorizationError | common_exceptions.InvalidToken | common_exceptions.TaskAlreadyExistsError |   common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        task = await self.task_repository.get_by_uuid(data.uuid)
        if isinstance(task, (common_exceptions.TaskNotFoundError, common_exceptions.TaskAlreadyExistsError, common_exceptions.RepositoryError)):
            raise task

        project_members = await self.project_repository.get_members([task.substage.project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members
        
        project = await self.project_repository.get_by_uuid(task.substage.project.uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project
        
        authorization_error = self.authorization_policy.decide_get_task(actor, project, project_members)
        if isinstance(authorization_error, exceptions.TaskAuthorizationError):
            raise authorization_error

        return dto.GetTaskOutDTO(task=task)


class UpdateTaskInteractor:
    def __init__(
        self,
        task_repository: common_interfaces.TaskRepository,
        user_repository: common_interfaces.UserRepository,
        stage_repository: common_interfaces.StageRepository,
        project_repository: common_interfaces.ProjectRepository,
        subscription_repository: common_interfaces.SubscriptionRepository,
        authorization_policy: interfaces.TaskAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        text_normalizer: common_interfaces.TextNormalizer,
        validator: validators.UpdateTaskValidator,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.stage_repository = stage_repository
        self.project_repository = project_repository
        self.subscription_repository = subscription_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.text_normalizer = text_normalizer
        self.validator = validator

    async def execute(self, data: dto.UpdateTaskInDTO) -> dto.UpdateTaskOutDTO | common_exceptions.TaskNotFoundError | common_exceptions.UserNotFoundError | exceptions.TaskAuthorizationError | common_exceptions.InvalidToken | common_exceptions.TaskAlreadyExistsError |  common_exceptions.RepositoryError:
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        task = await self.task_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(task, (common_exceptions.TaskNotFoundError, common_exceptions.TaskAlreadyExistsError, common_exceptions.RepositoryError)):
            raise task

        subscription = await self.project_repository.get_current_subscription(task.substage.project.uuid)
        if isinstance(subscription, common_exceptions.ProjectNotFoundError):
            raise subscription
        if isinstance(subscription, common_exceptions.SubscriptionNotFoundError):
            subscription = None
        if isinstance(subscription, common_exceptions.RepositoryError):
            raise subscription

        ensure_err = task.ensure_update(subscription)
        if ensure_err:
            raise exceptions.CantUpdateTask(ensure_err)

        project_members = await self.project_repository.get_members([task.substage.project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_update_task(actor, task, project_members)
        if isinstance(authorization_error, exceptions.TaskAuthorizationError):
            raise authorization_error

        update_data: dict[str, Any] = {}
        if data.name is not None:
            update_data['name'] = self.text_normalizer.normalize(data.name)
        if data.description is not None:
            update_data['description'] = self.text_normalizer.normalize(data.description)
        if data.substage_uuid is not None:
            substage = await self.stage_repository.get_by_uuid(data.substage_uuid)
            if isinstance(substage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
                raise substage
            update_data['substage'] = substage
        if data.completed is not None:
            update_data['completed'] = data.completed

        updated = await self.task_repository.update(data.uuid, update_data)
        if isinstance(updated, (common_exceptions.TaskNotFoundError, common_exceptions.TaskAlreadyExistsError, common_exceptions.RepositoryError)):
            raise updated

        await self.db_session.commit()
        return dto.UpdateTaskOutDTO(task=updated)


class DeleteTaskInteractor:
    def __init__(
        self,
        task_repository: common_interfaces.TaskRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.TaskAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.db_session = db_session
        self.context = context

    async def execute(self, data: dto.DeleteTaskInDTO) -> None | common_exceptions.TaskNotFoundError | common_exceptions.UserNotFoundError | exceptions.TaskAuthorizationError | common_exceptions.InvalidToken | common_exceptions.TaskAlreadyExistsError |  common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        task = await self.task_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(task, (common_exceptions.TaskNotFoundError, common_exceptions.TaskAlreadyExistsError, common_exceptions.RepositoryError)):
            raise task

        project_members = await self.project_repository.get_members([task.substage.project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_delete_task(actor, task, project_members)
        if isinstance(authorization_error, exceptions.TaskAuthorizationError):
            raise authorization_error

        delete_result = await self.task_repository.delete(data.uuid)
        if isinstance(delete_result, common_exceptions.RepositoryError):
            raise delete_result
        await self.db_session.commit()


class GetTaskListInteractor:
    def __init__(
        self,
        task_repository: common_interfaces.TaskRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        stage_repository: common_interfaces.StageRepository,
        authorization_policy: interfaces.TaskAuthorizationPolicy,
        context: common_interfaces.UserContext,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.stage_repository = stage_repository
        self.authorization_policy = authorization_policy
        self.context = context

    async def execute(self, data: dto.ListTasksInDTO) -> dto.ListTasksOutDTO | common_exceptions.StageNotFoundError | common_exceptions.UserNotFoundError | exceptions.TaskAuthorizationError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        substage = await self.stage_repository.get_by_uuid(data.substage_uuid)
        if isinstance(substage, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise substage

        project = substage.project
        project_members = await self.project_repository.get_members([project.uuid])
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_task(actor, project, project_members)
        if isinstance(authorization_error, exceptions.TaskAuthorizationError):
            raise authorization_error

        tasks = await self.task_repository.get_list(data.substage_uuid)
        if isinstance(tasks, (common_exceptions.StageNotFoundError, common_exceptions.RepositoryError)):
            raise tasks

        return dto.ListTasksOutDTO(tasks=tasks)
