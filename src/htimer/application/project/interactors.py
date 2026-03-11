from uuid import uuid4
from dataclasses import asdict
from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities
from . import exceptions, interfaces, validators, dto


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
        user_context: common_interfaces.Context,
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
        
    async def execute(self, data: dto.CreateProjectInDTO) -> dto.CreateProjectOutDTO:
        """Создаёт проект.

        Args:
            data: Структура CreateProjectInDTO.
                - name: str
                - description: str | None
                - start_date: str | None
                - end_date: str | None

        Returns:
            dto.CreateProjectOutDTO: Структура результата.
                - project: entities.Project

        Raises:
            exceptions.InvalidProjectDescriptionError: Описание проекта не прошло валидацию.
            exceptions.InvalidProjectNameError: Имя проекта не прошло валидацию.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            exceptions.ProjectAuthorizationError: Недостаточно прав для создания проекта.
            common_exceptions.UserAlreadyHasProjectError: У пользователя уже есть проект.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        

        if data.description is not None:
            data.description = self.text_normalizer.normalize(data.description)
        
        validation_error = self.create_project_validator.validate(data)
        if validation_error is not None:
            raise validation_error
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        actor = await self.user_repository.get_by_uuid(current_user_uuid)
        
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise common_exceptions.InvalidTokenError("Current user not found")
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
            created_at=await self.clock.now_date(),
        )

        created_project = await self.project_repository.create(new_project)
        if isinstance(created_project, (common_exceptions.UserAlreadyHasProjectError, common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise created_project

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
        user_context: common_interfaces.Context,
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
        
    async def execute(self, data: dto.UpdateProjectInDTO) -> dto.UpdateProjectOutDTO:
        """Обновляет проект.

        Args:
            data: Структура UpdateProjectInDTO.
                - uuid: UUID
                - name: str | None
                - description: str | None
                - status: entities.ProjectStatus | None
                - start_date: str | None
                - end_date: str | None

        Returns:
            dto.UpdateProjectOutDTO: Структура результата.
                - project: entities.Project

        Raises:
            exceptions.AllFieldsNoneError: Не переданы поля для обновления.
            exceptions.InvalidProjectDescriptionError: Описание проекта не прошло валидацию.
            exceptions.InvalidProjectNameError: Имя проекта не прошло валидацию.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.ProjectAuthorizationError: Недостаточно прав для обновления проекта.
            common_exceptions.SubscriptionNotFoundError: Активная подписка проекта не найдена.
            exceptions.CantUpdateProjectError: Нарушены доменные ограничения обновления проекта.
            common_exceptions.UserAlreadyHasProjectError: Конфликт уникальности проекта.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        

        if data.description is not None:
            data.description = self.text_normalizer.normalize(data.description)
        
        validation_error = self.update_project_validator.validate(data)
        if validation_error is not None:
            raise validation_error
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        actor = await self.user_repository.get_by_uuid(current_user_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor

        project = await self.project_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(project, common_exceptions.ProjectNotFoundError):
            raise project
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
        context: common_interfaces.Context,
        
    ):
        self.project_repository = project_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.user_repository = user_repository
        self.context = context
        
    async def execute(self, data: dto.GetProjectInDTO) -> dto.GetProjectsOutDTO:
        """Возвращает проект и его участников.

        Args:
            data: Структура GetProjectInDTO.
                - project_uuid: UUID

        Returns:
            dto.GetProjectsOutDTO: Структура результата.
                - project: entities.Project
                - members: list[entities.User]

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.ProjectAuthorizationError: Недостаточно прав для просмотра проекта.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, common_exceptions.ProjectNotFoundError):
            raise project

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
        user_context: common_interfaces.Context,
        validator: validators.GetProjectListValidator,
    ):
        self.user_repository = user_repository
        self.user_context = user_context
        self.validator = validator

    async def execute(self, data: dto.GetProjectListInDTO) -> dto.GetProjectListOutDTO:
        """Возвращает список проектов текущего пользователя.

        Args:
            data: Структура GetProjectListInDTO.
                - (полей нет)

        Returns:
            dto.GetProjectListOutDTO: Структура результата.
                - projects: list[entities.Project]

        Raises:
            exceptions.ProjectValidationError: Входные данные не прошли валидацию.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
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
        context: common_interfaces.Context,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
        clock: common_interfaces.Clock,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.db_session = db_session
        self.context = context
        self.authorization_policy = authorization_policy
        self.clock = clock
    
    async def execute(self, data: dto.AddMembersInDTO) -> dto.AddMembersOutDTO:
        """Добавляет участников в проект.

        Args:
            data: Структура AddMembersInDTO.
                - project_uuid: UUID
                - members_uuids: list[UUID]

        Returns:
            dto.AddMembersOutDTO: Структура результата.
                - members: list[entities.MemberShip]

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.ProjectAuthorizationError: Недостаточно прав для изменения состава проекта.
            common_exceptions.UserAlreadyProjectMemberError: Пользователь уже состоит в проекте.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
                
        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, common_exceptions.ProjectNotFoundError):
            raise project

        if isinstance(project, common_exceptions.RepositoryError):
            raise project
        
        project_members = await self.project_repository.get_members([project.uuid])
        
        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members
        
        
        authorization_error = self.authorization_policy.decide_update_project(
            actor,
            project, 
            project_members,
        )
        
        
        if authorization_error is not None:
            raise authorization_error
        
        assigned_by = actor
        
        added_users = await self.user_repository.get_list(data.members_uuids)
        if isinstance(added_users, common_exceptions.UserNotFoundError):
            raise added_users
        
        if isinstance(added_users, common_exceptions.RepositoryError):
            raise added_users
        
        members = [entities.MemberShip(
            uuid=uuid4(), 
            project=project,
            user=added_user,
            assigned_by=assigned_by,
            joined_at=await self.clock.now_date()
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
        context: common_interfaces.Context,
        authorization_policy: interfaces.ProjectAuthorizationPolicy,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.db_session = db_session
        self.context = context
        self.authorization_policy = authorization_policy
        
    async def execute(self, data: dto.RemoveMembersInDTO) -> None:
        """Удаляет участников из проекта.

        Args:
            data: Структура RemoveMembersInDTO.
                - project_uuid: UUID
                - members_uuids: list[UUID]

        Returns:
            None: Участники успешно удалены.

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.MemberNotFound: Участник проекта не найден.
            exceptions.ProjectAuthorizationError: Недостаточно прав для изменения состава проекта.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor
        
        if isinstance(actor, common_exceptions.RepositoryError):
            raise actor
        
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)

        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
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
        


        
 