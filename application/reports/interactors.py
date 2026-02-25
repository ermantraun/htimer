from uuid import uuid4
from . import dto, exceptions, interfaces, validators
from application import common_interfaces, common_exceptions
from domain import entities

class CreateReportRequestInteractor:
    def __init__(self, session: common_interfaces.DBSession, clock: common_interfaces.Clock, logger: common_interfaces.Logger, user_repository: common_interfaces.UserRepository, report_repository: common_interfaces.ReportRepository, project_repository: common_interfaces.ProjectRepository, job_gateway: common_interfaces.JobGateway, context: common_interfaces.Context, authorization_policy: interfaces.ReportsAuthorizationPolicy):
        self.session = session
        self.clock = clock
        self.logger = logger
        self.user_repository = user_repository
        self.report_repository = report_repository
        self.project_repository = project_repository
        self.job_gateway = job_gateway
        self.context = context
        self.authorization_policy = authorization_policy
        self.validator = validators.CreateReportRequestValidator

    async def execute(self, data: dto.CreateReportRequestInDTO) -> dto.CreateReportRequestOutDTO | common_exceptions.InvalidTokenError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError | exceptions.ReportAuthorizationError | common_exceptions.InvalidDate | common_exceptions.JobGatewayError | exceptions.InvalidPeriodError:
        
        validate_error = self.validator.validate(data)

        if validate_error:
            return validate_error

        start_date, end_date = None, None

        if data.start_date or data.end_date:
            verify_period_error = self.clock.verify_period(data.start_date, data.end_date)
            if verify_period_error:
                return verify_period_error


        actor = self.context.get_current_user_uuid()

        if isinstance(actor, common_exceptions.InvalidTokenError): 
            return actor
        
        actor = await self.user_repository.get_by_uuid(actor)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            return actor
        
        project = await self.project_repository.get_by_uuid(data.project_id)

        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            return project
        
        users = None

        if data.target_users is not None:
            users = await self.user_repository.get_list(data.target_users)

        if isinstance(users, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            return users
        
        if users is None:
            users = [actor]
        project_members = await self.project_repository.get_members([project.uuid])

        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            return project_members

        authorization_error = self.authorization_policy.decide_create_report(actor, project, project_members, users)

        if isinstance(authorization_error, exceptions.ReportAuthorizationError):
            return authorization_error

        report = entities.Report(
            uuid=uuid4(),
            project=project,
            creator=actor,
            generated_at=await self.clock.now_date(),
            target_users=users,
            start_date=start_date,
            end_date=end_date
        )

        create_report_error = await self.report_repository.create(report)
        if isinstance(create_report_error, (common_exceptions.RepositoryError, common_exceptions.ProjectNotFoundError, common_exceptions.UserNotFoundError)):
            return create_report_error
        
        enqueue_error = await self.job_gateway.enqueue_report_generation(report)
        if isinstance(enqueue_error, common_exceptions.JobGatewayError):
            return enqueue_error

        await self.logger.info(message=f"Report {report.uuid} creation requested by user {actor.uuid} for project {project.uuid} with target users {[user.uuid for user in users]} and period {start_date} to {end_date}", operation="create_report_request")

        await self.session.commit()

        return dto.CreateReportRequestOutDTO(report=report)
    
class CreateReportInteractor:
    def __init__(self, create_report_request_interactor: CreateReportRequestInteractor):
        self.create_report_request_interactor = create_report_request_interactor

    async def execute(self) -> None:

        pass