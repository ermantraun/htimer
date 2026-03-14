from uuid import uuid4

from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities

from . import dto, exceptions, interfaces, validators


class CreateDailyLogInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.Context,
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

        # file storage will be injected into interactors that need upload/download links

    async def execute(self, data: dto.CreateDailyLogInDTO) -> dto.CreateDailyLogOutDTO:
        """Создаёт запись дня проекта.

        Args:
            data: Структура CreateDailyLogInDTO.
                - date: str
                - creator_uuid: UUID
                - project_uuid: UUID
                - draft: bool
                - hours_spent: float
                - description: str
                - substage_uuid: UUID | None

        Returns:
            dto.CreateDailyLogOutDTO: Структура результата.
                - daily_log: entities.DailyLog

        Raises:
            exceptions.DayliLogValidationError: Входные данные не прошли валидацию.
            common_exceptions.InvalidDate: Передана некорректная дата.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для создания записи дня.
            common_exceptions.StageNotFoundError: Указанный этап не найден.
            common_exceptions.DailyLogAlreadyExistsError: Запись дня уже существует.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """

        validation_error = self.validator.validate(data)

        clock_error = self.clock.verify_date(data.date)

        if isinstance(clock_error, common_exceptions.InvalidDate):
            raise clock_error

        if validation_error is not None:
            raise validation_error

        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        project_members = await self.project_repository.get_members([project.uuid])
        if isinstance(
            project_members,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project_members

        authorization_error = self.authorization_policy.decide_create_daily_log(
            actor, project, project_members
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        daily_log = await self.daily_log_repository.create(
            data=entities.DailyLog(
                uuid=uuid4(),
                creator=actor,
                project=project,
                draft=data.draft,
                created_at=await self.clock.now_date(),
                description=self.text_normalizer.normalize(data.description)
                if data.description
                else data.description,
                hours_spent=data.hours_spent,
            )
        )

        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogAlreadyExistsError,
                common_exceptions.UserNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.DailyLogAlreadyExistsError,
                common_exceptions.StageNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        await self.db_session.commit()

        return dto.CreateDailyLogOutDTO(daily_log=daily_log)


class UpdateDailyLogInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.Context,
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

    async def execute(self, data: dto.UpdateDailyLogInDTO) -> dto.UpdateDailyLogOutDTO:
        """Обновляет запись дня.

        Args:
            data: Структура UpdateDailyLogInDTO.
                - uuid: UUID
                - draft: bool | None
                - hours_spent: float | None
                - description: str | None
                - substage_uuid: UUID | None

        Returns:
            dto.UpdateDailyLogOutDTO: Структура результата.
                - daily_log: entities.DailyLog

        Raises:
            exceptions.DayliLogValidationError: Входные данные не прошли валидацию.
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для обновления записи дня.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        validation_error = self.validator.validate(data)

        if validation_error is not None:
            raise validation_error

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(
            data.uuid, lock_record=True
        )
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(
            actor, daily_log
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        update_data: dict[str, object] = {}

        if data.description is not None:
            update_data["description"] = self.text_normalizer.normalize(
                data.description
            )
            update_data["updated_at"] = self.clock.now_date()

        if data.hours_spent is not None:
            update_data["hours_spent"] = data.hours_spent
            update_data["updated_at"] = self.clock.now_date()

        if data.substage_uuid is not None:
            update_data["substage_uuid"] = data.substage_uuid
            update_data["updated_at"] = self.clock.now_date()

        if data.draft is not None:
            update_data["draft"] = data.draft
            update_data["updated_at"] = self.clock.now_date()

        updated = await self.daily_log_repository.update(data.uuid, update_data)
        if isinstance(
            updated,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
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
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.context = context
        self.project_repository = project_repository

    async def execute(self, data: dto.GetDailyLogInDTO) -> dto.GetDailyLogOutDTO:
        """Возвращает запись дня по идентификатору.

        Args:
            data: Структура GetDailyLogInDTO.
                - uuid: UUID

        Returns:
            dto.GetDailyLogOutDTO: Структура результата.
                - daily_log: entities.DailyLog

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для просмотра записи дня.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.uuid)
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        project_members = await self.project_repository.get_members(
            [daily_log.project.uuid]
        )

        if isinstance(
            project_members,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log(
            actor, daily_log, project_members
        )
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
        file_storage: common_interfaces.FileStorage,
        db_session: common_interfaces.DBSession,
        clock: common_interfaces.Clock,
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.file_repository = file_repository
        self.db_session = db_session
        self.clock = clock
        self.context = context
        self.file_storage = file_storage

    async def execute(
        self, data: dto.CreateDailyLogFileInDTO
    ) -> dto.CreateDailyLogFileOutDTO:
        """Создаёт файл записи дня и выдаёт ссылку на загрузку.

        Args:
            data: Структура CreateDailyLogFileInDTO.
                - daily_log_uuid: UUID
                - filename: str

        Returns:
            dto.CreateDailyLogFileOutDTO: Структура результата.
                - file: entities.DailyLogFile
                - action_link: ActionLink

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для изменения записи дня.
            common_exceptions.FileAlreadyExistsError: Файл уже существует в репозитории.
            common_exceptions.FileAlreadyExistsInStorageError: Файл уже существует в хранилище.
            common_exceptions.FileStorageError: Ошибка файлового хранилища.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(
            actor, daily_log
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        file = entities.DailyLogFile(
            uuid=uuid4(),
            filename=data.filename,
            daily_log=daily_log,
            uploaded_at=await self.clock.now_date(),
            uri=daily_log.uuid.hex + "/" + data.filename,
        )

        stored = await self.file_repository.create(file)
        if isinstance(
            stored,
            (
                common_exceptions.FileAlreadyExistsError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise stored

        storage_result = await self.file_storage.get_upload_link(str(stored.uuid))
        if isinstance(
            storage_result,
            (
                common_exceptions.FileAlreadyExistsInStorageError,
                common_exceptions.FileStorageError,
            ),
        ):
            raise storage_result

        await self.db_session.commit()

        return dto.CreateDailyLogFileOutDTO(
            file=stored, action_link=common_interfaces.ActionLink(storage_result)
        )


class GetDailyLogFileInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        file_repository: common_interfaces.FileRepository,
        file_storage: common_interfaces.FileStorage,
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.file_repository = file_repository
        self.context = context
        self.file_storage = file_storage

    async def execute(
        self, data: dto.GetDailyLogFileInDTO
    ) -> dto.GetDailyLogFileOutDTO:
        """Возвращает файл записи дня и ссылку на скачивание.

        Args:
            data: Структура GetDailyLogFileInDTO.
                - daily_log_uuid: UUID
                - file_uuid: UUID

        Returns:
            dto.GetDailyLogFileOutDTO: Структура результата.
                - file: entities.DailyLogFile
                - action_link: ActionLink

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для просмотра файла.
            common_exceptions.FileNotFoundError: Файл не найден в репозитории.
            common_exceptions.FileNotFoundInStorageError: Файл не найден в хранилище.
            common_exceptions.FileStorageError: Ошибка файлового хранилища.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        project_members = await self.project_repository.get_members(
            [daily_log.project.uuid]
        )
        if isinstance(
            project_members,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log(
            actor, daily_log, project_members
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        found = await self.file_repository.get(data.file_uuid)
        if isinstance(
            found,
            (common_exceptions.FileNotFoundError, common_exceptions.RepositoryError),
        ):
            raise found

        storage_result = await self.file_storage.get_unload_link(str(found.uuid))
        if isinstance(
            storage_result,
            (
                common_exceptions.FileNotFoundInStorageError,
                common_exceptions.FileStorageError,
            ),
        ):
            raise storage_result

        return dto.GetDailyLogFileOutDTO(
            file=found, action_link=common_interfaces.ActionLink(storage_result)
        )


class RemoveDailyLogFileInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        file_repository: common_interfaces.FileRepository,
        file_storage: common_interfaces.FileStorage,
        db_session: common_interfaces.DBSession,
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.file_repository = file_repository
        self.file_storage = file_storage
        self.db_session = db_session
        self.context = context

    async def execute(
        self, data: dto.RemoveDailyLogFileInDTO
    ) -> dto.GetDailyLogFileOutDTO:
        """Удаляет файл записи дня.

        Args:
            data: Структура RemoveDailyLogFileInDTO.
                - daily_log_uuid: UUID
                - file_uuid: UUID

        Returns:
            dto.GetDailyLogFileOutDTO: Структура результата.
                - file: entities.DailyLogFile
                - action_link: ActionLink

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для изменения записи дня.
            common_exceptions.FileNotFoundError: Файл не найден в репозитории.
            common_exceptions.FileNotFoundInStorageError: Файл не найден в хранилище.
            common_exceptions.FileStorageError: Ошибка файлового хранилища.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(
            data.daily_log_uuid, lock_record=True
        )
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        authorization_error = self.authorization_policy.decide_update_daily_log(
            actor, daily_log
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        removed = await self.file_repository.remove(data.file_uuid)
        if isinstance(
            removed,
            (common_exceptions.FileNotFoundError, common_exceptions.RepositoryError),
        ):
            raise removed

        storage_result = await self.file_storage.remove(str(removed.uuid))
        if isinstance(
            storage_result,
            (
                common_exceptions.FileNotFoundInStorageError,
                common_exceptions.FileStorageError,
            ),
        ):
            raise storage_result

        await self.db_session.commit()

        return dto.GetDailyLogFileOutDTO(
            file=removed, action_link=common_interfaces.ActionLink(None)
        )


class GetDailyLogFileListInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        project_repository: common_interfaces.ProjectRepository,
        file_repository: common_interfaces.FileRepository,
        file_storage: common_interfaces.FileStorage,
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.file_repository = file_repository
        self.context = context
        self.file_storage = file_storage

    async def execute(
        self, data: dto.GetDailyLogFileListInDTO
    ) -> dto.GetDailyLogFileListOutDTO:
        """Возвращает список файлов записи дня с ссылками на скачивание.

        Args:
            data: Структура GetDailyLogFileListInDTO.
                - daily_log_uuid: UUID

        Returns:
            dto.GetDailyLogFileListOutDTO: Структура результата.
                - files: list[tuple[entities.DailyLogFile, ActionLink]]

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.DailyLogNotFoundError: Запись дня не найдена.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для просмотра файлов.
            common_exceptions.FileNotFoundError: Файлы не найдены в репозитории.
            common_exceptions.FileNotFoundInStorageError: Файлы не найдены в хранилище.
            common_exceptions.FileStorageError: Ошибка файлового хранилища.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        daily_log = await self.daily_log_repository.get_by_uuid(data.daily_log_uuid)
        if isinstance(
            daily_log,
            (
                common_exceptions.DailyLogNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise daily_log

        project_members = await self.project_repository.get_members(
            [daily_log.project.uuid]
        )
        if isinstance(
            project_members,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log(
            actor, daily_log, project_members
        )
        if isinstance(authorization_error, exceptions.DayliLogAuthorizationError):
            raise authorization_error

        files = await self.file_repository.get_list(data.daily_log_uuid)
        if isinstance(
            files,
            (common_exceptions.FileNotFoundError, common_exceptions.RepositoryError),
        ):
            raise files

        storage_result = await self.file_storage.get_unload_link_list(
            [str(f.uuid) for f in files]
        )
        if isinstance(
            storage_result,
            (
                common_exceptions.FileNotFoundInStorageError,
                common_exceptions.FileStorageError,
            ),
        ):
            raise storage_result

        uuid_to_file = {str(f.uuid): f for f in files}
        paired = [
            (uuid_to_file[file_name], common_interfaces.ActionLink(link))
            for file_name, link in storage_result
        ]
        return dto.GetDailyLogFileListOutDTO(files=paired)


class GetDailyLogListInteractor:
    def __init__(
        self,
        daily_log_repository: common_interfaces.DailyLogRepository,
        project_repository: common_interfaces.ProjectRepository,
        user_repository: common_interfaces.UserRepository,
        authorization_policy: interfaces.DailyLogAuthorizationPolicy,
        context: common_interfaces.Context,
    ):
        self.daily_log_repository = daily_log_repository
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.authorization_policy = authorization_policy
        self.context = context

    async def execute(
        self, data: dto.GetDailyLogListInDTO
    ) -> dto.GetDailyLogListOutDTO:
        """Возвращает список записей дня проекта.

        Args:
            data: Структура GetDailyLogListInDTO.
                - project_uuid: UUID
                - start_date: date
                - end_date: date
                - user_uuid: UUID | None

        Returns:
            dto.GetDailyLogListOutDTO: Структура результата.
                - daily_logs: list[entities.DailyLog]

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            exceptions.DayliLogAuthorizationError: Недостаточно прав для просмотра списка.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        actor_uuid = self.context.get_current_user_uuid()

        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(
            actor,
            (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError),
        ):
            raise actor

        target = actor

        if data.user_uuid is not None:
            target = await self.user_repository.get_by_uuid(data.user_uuid)

            if isinstance(
                target,
                (
                    common_exceptions.UserNotFoundError,
                    common_exceptions.RepositoryError,
                ),
            ):
                raise target

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(
            project,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project

        project_members = await self.project_repository.get_members([project.uuid])

        if isinstance(
            project_members,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise project_members

        authorization_error = self.authorization_policy.decide_get_daily_log_list(
            actor, target, project, project_members
        )
        if authorization_error is not None:
            raise authorization_error

        daily_logs = await self.daily_log_repository.get_list_by_project(
            project.uuid, data.start_date, data.end_date, [target.uuid], draft=False
        )
        if isinstance(
            daily_logs,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise daily_logs

        return dto.GetDailyLogListOutDTO(daily_logs=daily_logs)
