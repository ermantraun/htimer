from uuid import uuid4, UUID
from . import dto, exceptions, interfaces, validators
from htimer.application import common_interfaces, common_exceptions
from htimer.domain import entities

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

    async def execute(self, data: dto.CreateReportRequestInDTO) -> dto.CreateReportRequestOutDTO:
        """Создаёт запрос на генерацию отчёта.

        Args:
            data: Структура CreateReportRequestInDTO.
                - project_id: UUID
                - start_date: date | None
                - end_date: date | None
                - target_users: list[UUID] | None

        Returns:
            dto.CreateReportRequestOutDTO: Структура результата.
                - report: entities.Report

        Raises:
            exceptions.InvalidPeriodError: Передан некорректный период отчёта.
            common_exceptions.InvalidDate: Переданы некорректные даты.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.ReportAuthorizationError: Недостаточно прав для создания отчёта.
            common_exceptions.JobGatewayError: Ошибка постановки задания на генерацию отчёта.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        
        validate_error = self.validator.validate(data)

        if validate_error:
            raise validate_error

        start_date, end_date = None, None

        if data.start_date or data.end_date:
            verify_period_error = self.clock.verify_period(data.start_date, data.end_date)
            if verify_period_error:
                raise verify_period_error


        actor = self.context.get_current_user_uuid()

        if isinstance(actor, common_exceptions.InvalidTokenError): 
            raise actor
        
        actor = await self.user_repository.get_by_uuid(actor)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor
        
        project = await self.project_repository.get_by_uuid(data.project_id)

        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project
        
        users = None

        if data.target_users is not None:
            users = await self.user_repository.get_list(data.target_users)

        if isinstance(users, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise users

        project_members = await self.project_repository.get_members([project.uuid])

        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project_members

        authorization_error = self.authorization_policy.decide_create_report(actor, project, project_members, users)

        if isinstance(authorization_error, exceptions.ReportAuthorizationError):
            raise authorization_error

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
            raise create_report_error
        
        enqueue_error = await self.job_gateway.publish_report(report.uuid)
        if isinstance(enqueue_error, (common_exceptions.RepositoryError, common_exceptions.JobGatewayError)):
            raise enqueue_error

        await self.logger.info(message=f"Report {report.uuid} creation requested by user {actor.uuid} for project {project.uuid} with period {start_date} to {end_date}", operation="create_report_request")

        await self.session.commit()

        return dto.CreateReportRequestOutDTO(report=report)
    

class CreateReportInteractor:
    def __init__(self, file_storage: common_interfaces.FileStorage, visualizer: interfaces.ReportVizualizer, project_repository: common_interfaces.ProjectRepository,  report_repository: common_interfaces.ReportRepository, logger: common_interfaces.Logger, daily_log_repository: common_interfaces.DailyLogRepository, task_repository: common_interfaces.TaskRepository):
        self.visualizer = visualizer
        self.project_repository = project_repository
        self.report_repository = report_repository
        self.logger = logger
        self.daily_log_repository = daily_log_repository
        self.task_repository = task_repository
        self.file_storage = file_storage


    async def execute(self, dto: dto.CreateReportInDTO) -> None:
        """Генерирует содержимое отчёта и сохраняет файл.

        Args:
            dto: Структура CreateReportInDTO.
                - report_id: str

        Returns:
            None: Отчёт успешно сформирован и сохранён.

        Raises:
            common_exceptions.ReportNotFoundError: Отчёт не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.ReportCreateError: Ошибка формирования содержимого отчёта.
            common_exceptions.FileAlreadyExistsInStorageError: Файл отчёта уже существует в хранилище.
            common_exceptions.FileStorageError: Ошибка файлового хранилища.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        report = await self.report_repository.get_by_uuid(UUID(dto.report_id))

        if isinstance(report, (common_exceptions.ReportNotFoundError, common_exceptions.RepositoryError)):
            await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to report not found", operation="report_generation_failed")
            raise report
        
        project_members = await self.project_repository.get_members([report.project.uuid])

        if isinstance(project_members, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to project not found", operation="report_generation_failed")
            raise project_members

        daily_logs = await self.daily_log_repository.get_list_by_project(report.project.uuid, report.start_date, report.end_date, [member.uuid for member in project_members], draft=False)
        
        if isinstance(daily_logs, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to error fetching daily logs", operation="report_generation_failed")
            raise daily_logs

        if report.is_summary_report():
            tasks = await self.task_repository.get_list_by_project(report.project.uuid)

        

            if isinstance(tasks, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
                await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to error fetching tasks", operation="report_generation_failed")
                raise tasks

            report_content = report.make_summary_report_content(daily_logs, tasks)

        else:
            report_content = report.make_activity_report_content(daily_logs)

        visualization = self.visualizer.vizualize(report_content)


        report.mark_completed(file_name=f"{report.uuid}")


        report_update_error = await self.report_repository.update(report.uuid, {
            "status": report.status,
            "file_name": report.file_name
        })

        if isinstance(report_update_error, (common_exceptions.RepositoryError, common_exceptions.ReportNotFoundError)):
            await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to error updating report status", operation="report_generation_failed")
            raise report_update_error

        error = await self.file_storage.save(file_name=f"{report.uuid}", content=visualization)

        if isinstance(error, (common_exceptions.FileAlreadyExistsInStorageError, common_exceptions.FileStorageError)):
            await self.logger.info(message=f"Report generation failed for report {dto.report_id} due to error saving report file", operation="report_generation_failed")
            raise error
       

        

