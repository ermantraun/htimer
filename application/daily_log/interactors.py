from uuid import uuid4
from application import common_exceptions, common_interfaces
from domain import entities
import dto, interfaces, exceptions, validators


class CreateDailyLogInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        text_normalizer: common_interfaces.TextNormalizer,
        validator: validators.CreateDailyLogValidator,
        
    ):
        self.daily_log_repository = daily_log_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.clock = clock
        self.validator = validator
        self.text_normalizer = text_normalizer
    
    async def execute(self, data: dto.CreateDailyLogInDTO) -> dto.CreateDailyLogOutDTO | common_exceptions.DailyLogAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.DayliLogAuthorizationError | common_exceptions.StageNotFoundError | common_exceptions.InvalidDate | common_exceptions.InvalidToken:
        
        validation_error = self.validator.validate(data)
        
        clock_error = self.clock.verify_date()
        
        if isinstance(clock_error, common_exceptions.InvalidDate):
            raise clock_error
        
        if validation_error is not None:
            raise validation_error
        
        actor_uuid = self.context.get_current_user_uuid()
        
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid
        
        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor
        
        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, common_exceptions.ProjectNotFoundError):
            raise project
        
        project_members = await self.project_repository.get_members([project.uuid])
        if isinstance(project_members, common_exceptions.ProjectNotFoundError):
            raise project_members
        
        authorization_error = self.authorization_policy.decide_create_daily_log(actor, project, project_members)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        daily_log = await self.daily_log_repository.create(
            data=entities.DailyLog(
                uuid=uuid4(),
                creator=actor,
                project=project,
                draft = data.draft,
                created_at=self.clock.now_date(),
                description=self.text_normalizer.normalize(data.description) if data.description else data.description,
                hours_spent=data.hours_spent,
            )
        )
        
        if isinstance(daily_log, (common_exceptions.DailyLogAlreadyExistsError, common_exceptions.UserNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.DailyLogAlreadyExistsError, common_exceptions.StageNotFoundError)):
            raise daily_log
        
        await self.db_session.commit()
        
        return dto.CreateDailyLogOutDTO(
            daily_log=daily_log
        )
        
        

class UpdateDailyLogInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        text_normalizer: common_interfaces.TextNormalizer,
        validator: validators.UpdateDailyLogValidator,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.db_session = db_session
        self.context = context
        self.clock = clock
        self.validator = validator
        self.text_normalizer = text_normalizer

    async def execute(self, data: dto.UpdateDailyLogInDTO) -> dto.UpdateDailyLogOutDTO | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.DayliLogAuthorizationError | common_exceptions.InvalidToken:
        validation_error = self.validator.validate(data)

        if validation_error is not None:
            raise validation_error

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.uuid, lock_record=True)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(actor, daily_log)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        update_data: dict[str, object] = {}

        if data.description is not None:
            update_data['description'] = self.text_normalizer.normalize(data.description)
            update_data['updated_at'] = self.clock.now_date()

        if data.hours_spent is not None:
            update_data['hours_spent'] = data.hours_spent
            update_data['updated_at'] = self.clock.now_date()

        if data.substage_uuid is not None:
            update_data['substage_uuid'] = data.substage_uuid
            update_data['updated_at'] = self.clock.now_date()
            
        if data.draft is not None:
            update_data['draft'] = data.draft
            update_data['updated_at'] = self.clock.now_date()
        
        
        updated = await self.daily_log_repository.update(data.uuid, update_data, release_record=True)
        if isinstance(updated, common_exceptions.DailyLogNotFoundError):
            raise updated

        await self.db_session.commit()

        return dto.UpdateDailyLogOutDTO(daily_log=updated)

class GetDailyLogInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.context = context
        self.project_repository = project_repository
        
    async def execute(self, data: dto.GetDailyLogInDTO) -> dto.GetDailyLogOutDTO | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.uuid)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        project_members = await self.project_repository.get_members([daily_log.project.uuid])
        
        if isinstance(project_members, common_exceptions.ProjectNotFoundError):
            raise project_members
        
        authorization_error = self.authorization_policy.decide_get_daily_log(actor, daily_log, project_members)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        return dto.GetDailyLogOutDTO(daily_log=daily_log)
        


class CreateDailyLogFileInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        file_repository: common_interfaces.FileRepository,
        db_session: common_interfaces.DBSession,
        clock: common_interfaces.Clock,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.file_repository = file_repository
        self.db_session = db_session
        self.clock = clock
        self.context = context

    async def execute(self, data: dto.CreateDailyLogFileInDTO) -> dto.CreateDailyLogFileOutDTO | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | exceptions.DayliLogAuthorizationError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(actor, daily_log)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        file = entities.File(
            uuid=uuid4(),
            filename=data.filename,
            day_entry=daily_log,
            uploaded_at=self.clock.now_date(),
            url = daily_log.uuid.hex + '/' + data.filename,
            
        )

        stored = await self.file_repository.create(file)

        await self.db_session.commit()

        return dto.CreateDailyLogFileOutDTO(file=stored)


class GetDailyLogFileInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        file_repository: common_interfaces.FileRepository,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.file_repository = file_repository
        self.context = context

    async def execute(self, data: dto.GetDailyLogFileInDTO) -> dto.GetDailyLogFileOutDTO | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | exceptions.DayliLogAuthorizationError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        project_members = await self.project_repository.get_members([daily_log.project.uuid])
        if isinstance(project_members, common_exceptions.ProjectNotFoundError):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log(actor, daily_log, project_members)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        found = await self.file_repository.get(data.daily_log_uuid, data.file_uuid)
        return dto.GetDailyLogFileOutDTO(file=found)


class RemoveDailyLogFileInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        file_repository: common_interfaces.FileRepository,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.file_repository = file_repository
        self.db_session = db_session
        self.context = context
    async def execute(self, data: dto.RemoveDailyLogFileInDTO) -> entities.File | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | exceptions.DayliLogAuthorizationError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid, lock_record=True)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(actor, daily_log)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        removed = await self.file_repository.remove(data.daily_log_uuid, data.file_uuid)

        await self.db_session.commit()

        return removed


class GetDailyLogFileListInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        file_repository: common_interfaces.FileRepository,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.file_repository = file_repository
        self.context = context

    async def execute(self, data: dto.GetDailyLogFileListInDTO) -> dto.GetDailyLogFileListOutDTO | common_exceptions.DailyLogNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | exceptions.DayliLogAuthorizationError:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(daily_log, common_exceptions.DailyLogNotFoundError):
            raise daily_log

        project_members = await self.project_repository.get_members([daily_log.project.uuid])
        if isinstance(project_members, common_exceptions.ProjectNotFoundError):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log(actor, daily_log, project_members)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        files = await self.file_repository.get_list(data.daily_log_uuid)
        return dto.GetDailyLogFileListOutDTO(files=files)
        


class GetDailyLogListInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        context: common_interfaces.UserContext,
    ):
        self.daily_log_repository = daily_log_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.context = context

    async def execute(self, data: dto.GetDailyLogListInDTO) -> dto.GetDailyLogListOutDTO | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | exceptions.DayliLogAuthorizationError | common_exceptions.InvalidToken:
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, common_exceptions.UserNotFoundError):
            raise actor

        target = actor
        
        if data.user_uuid is not None:
            target = await self.user_repository.get_by_uuid(data.user_uuid)

            if isinstance(target, common_exceptions.UserNotFoundError):
                raise target
            
        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, common_exceptions.ProjectNotFoundError):
            raise project

        project_members = await self.project_repository.get_members([project.uuid])
        
        if isinstance(project_members, common_exceptions.ProjectNotFoundError):
            raise project_members
        
        authorization_error = self.authorization_policy.decide_get_daily_log_list(actor, target, project, project_members)
        if authorization_error is not None:
            raise authorization_error

        daily_logs = await self.daily_log_repository.get_list(project.uuid, data.date)
        if isinstance(daily_logs, common_exceptions.ProjectNotFoundError):
            raise daily_logs

        return dto.GetDailyLogListOutDTO(daily_logs=daily_logs)





