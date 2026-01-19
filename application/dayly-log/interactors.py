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
        authorization_policy: interfaces.DailyLogCreateAuthorizationPolicy,
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
        
        authorization_error = self.authorization_policy.decide_create_daily_log(project_members)
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        daily_log = await self.daily_log_repository.create(
            data=entities.DailyLog(
                uuid=uuid4(),
                creator=actor,
                project=project,
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