from uuid import uuid4

from htimer.application import common_exceptions, common_interfaces
from htimer.domain import entities

from . import dto, exceptions, interfaces, validators


class CreateUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        context: common_interfaces.Context,
        user_repository: common_interfaces.UserRepository,
        hash_generator: interfaces.HashGenerator,
        validator: validators.CreateUserValidator,
        user_policy: interfaces.UserAuthorizationPolicy,
        clock: common_interfaces.Clock,
        logger: common_interfaces.Logger,
    ):
        self.user_repository = user_repository
        self.validator = validator
        self.context = context
        self.hash_generator = hash_generator
        self.session = session
        self.policy = user_policy
        self.clock = clock
        self.logger = logger

    async def execute(self, data: dto.CreateUserInDTO) -> dto.CreateUserOutDTO:
        """Создаёт пользователя.

        Args:
            data: Структура CreateUserInDTO.
                - name: str
                - email: str
                - password: str
                - role: entities.UserRole

        Returns:
            dto.CreateUserOutDTO: Структура результата.
                - user_uuid: UUID

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Текущий пользователь не найден.
            exceptions.UserValidationError: Входные данные не прошли валидацию.
            exceptions.UserAuthorizationError: Недостаточно прав для создания пользователя.
            common_exceptions.EmailAlreadyExistsError: Пользователь с таким email уже существует.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        current_user_uuid = self.context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        current_user = await self.user_repository.get_by_uuid(current_user_uuid)
        if isinstance(current_user, common_exceptions.UserNotFoundError):
            raise current_user
        if isinstance(current_user, common_exceptions.RepositoryError):
            raise current_user

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        auth_error = self.policy.decide_create_user(current_user)
        if auth_error is not None:
            raise auth_error

        password_hash = self.hash_generator.generate(data.password)

        new_user = entities.User(
            uuid=uuid4(),
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            creator=current_user,
            created_at=await self.clock.now_date(),
            role=data.role,
        )
        created_user = await self.user_repository.create(new_user)

        if isinstance(created_user, common_exceptions.EmailAlreadyExistsError):
            raise created_user
        if isinstance(created_user, common_exceptions.RepositoryError):
            raise created_user

        await self.session.commit()

        await self.logger.info(
            operation="CreateUser",
            message=f"User {created_user.uuid} created by {current_user.uuid}",
        )

        return dto.CreateUserOutDTO(user_uuid=created_user.uuid)


class GetUsersListInteractor:
    def __init__(
        self,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.Context,
        project_repository: common_interfaces.ProjectRepository,
        validator: validators.GetUsersListValidator,
        user_policy: interfaces.UserAuthorizationPolicy,
    ):

        self.user_context = context
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.validator = validator
        self.policy = user_policy

    async def execute(self, data: dto.GetUserListInDTO) -> dto.GetUserListOutDTO:
        """Возвращает список пользователей по проектам.

        Args:
            data: Структура GetUserListInDTO.
                - projects_names: set[str]
                - is_active: bool | None

        Returns:
            dto.GetUserListOutDTO: Структура результата.
                - users: list[entities.User]

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            exceptions.UserAuthorizationError: Недостаточно прав для просмотра списка.
            exceptions.UserValidationError: Входные данные не прошли валидацию.
            common_exceptions.ProjectNotFoundError: Проект не найден.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        current_user = await self.user_repository.get_by_uuid(current_user_uuid)
        if isinstance(current_user, common_exceptions.UserNotFoundError):
            raise current_user
        if isinstance(current_user, common_exceptions.RepositoryError):
            raise current_user

        user_projects = await self.user_repository.get_projects(current_user_uuid)
        if isinstance(
            user_projects,
            (
                common_exceptions.UserNotFoundError,
                common_exceptions.ProjectNotFoundError,
                common_exceptions.RepositoryError,
            ),
        ):
            raise user_projects

        user_projects_names = {p.name for p in user_projects}

        auth_error = self.policy.decide_get_users_list(
            actor=current_user,
            projects_names=data.projects_names,
            actor_projects_names=user_projects_names,
        )
        if auth_error is not None:
            raise auth_error

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        projects_uuid = [project.uuid for project in user_projects]

        users = await self.project_repository.get_members(
            projects_uuid=projects_uuid,
            is_active=data.is_active if data.is_active is not None else False,
        )

        if isinstance(
            users,
            (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError),
        ):
            raise users

        return dto.GetUserListOutDTO(users=users)


class LoginUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        hash_generator: interfaces.HashVerifier,
        context: common_interfaces.Context,
        validator: validators.LoginUserValidator,
        token_generator: interfaces.TokenGenerator,
        clock: common_interfaces.Clock,
        logger: common_interfaces.Logger,
    ):
        self.session = session
        self.user_repository = user_repository
        self.hash_generator = hash_generator
        self.context = context
        self.validator = validator
        self.token_generator = token_generator
        self.clock = clock
        self.logger = logger

    async def execute(self, data: dto.LoginUserInDTO) -> dto.LoginUserOutDTO:
        """Аутентифицирует пользователя и выдаёт токен.

        Args:
            data: Структура LoginUserInDTO.
                - email: str
                - password: str

        Returns:
            dto.LoginUserOutDTO: Структура результата.
                - token: str
                - user_uuid: UUID

        Raises:
            exceptions.UserValidationError: Входные данные не прошли валидацию.
            exceptions.InvalidCredentialsError: Указаны неверные учётные данные.
            common_exceptions.EmailAlreadyExistsError: Конфликт email при обновлении данных входа.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        user = await self.user_repository.get_by_email(data.email)
        if isinstance(user, common_exceptions.UserNotFoundError):
            raise exceptions.InvalidCredentialsError("Неверные учетные данные.")
        if isinstance(user, common_exceptions.RepositoryError):
            raise user

        if not self.hash_generator.verify(data.password, user.password_hash):
            raise exceptions.InvalidCredentialsError("Неверные учетные данные.")

        updated_user = await self.user_repository.update(
            user.uuid,
            {
                "last_login": self.clock.now_date(),
            },
        )
        if isinstance(updated_user, common_exceptions.EmailAlreadyExistsError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.UserNotFoundError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user

        await self.session.commit()

        await self.logger.info(
            operation="LoginUser", message=f"User {user.uuid} logged in"
        )

        return dto.LoginUserOutDTO(
            token=await self.token_generator.generate(user.uuid),
            user_uuid=user.uuid,
        )


class ResetUserPasswordInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.Context,
        hash_generator: interfaces.HashGenerator,
        validator: validators.ResetUserPasswordValidator,
        user_policy: interfaces.UserAuthorizationPolicy,
    ):
        self.session = session
        self.user_repository = user_repository
        self.user_context = context
        self.hash_generator = hash_generator
        self.validator = validator
        self.policy = user_policy

    async def execute(self, data: dto.ResetUserPasswordInDTO) -> None:
        """Сбрасывает пароль пользователя.

        Args:
            data: Структура ResetUserPasswordInDTO.
                - user_uuid: UUID | None
                - new_password: str

        Returns:
            None: Пароль успешно обновлён.

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            exceptions.UserAuthorizationError: Недостаточно прав для сброса пароля.
            exceptions.CantResetPasswordError: Сброс пароля невозможен по доменным ограничениям.
            exceptions.UserValidationError: Новый пароль не прошёл валидацию.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        target_user = None
        current_user = None

        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        current_user = await self.user_repository.get_by_uuid(
            current_user_uuid, lock_record=True
        )
        if isinstance(current_user, common_exceptions.UserNotFoundError):
            raise current_user
        if isinstance(current_user, common_exceptions.RepositoryError):
            raise current_user

        if data.user_uuid is None:
            target_user = current_user

        else:
            target_user = await self.user_repository.get_by_uuid(
                data.user_uuid, lock_record=True
            )
            if isinstance(target_user, common_exceptions.UserNotFoundError):
                raise target_user
            if isinstance(target_user, common_exceptions.RepositoryError):
                raise target_user

        auth_error = self.policy.decide_reset_user_password(
            actor=current_user,  # type: ignore
            target=target_user,
        )

        if auth_error is not None:
            raise auth_error

        if error := current_user.ensure_reset_password(target_user):  # type: ignore
            raise exceptions.CantResetPasswordError(error)

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        hashed_password = self.hash_generator.generate(data.new_password)

        updated_user = await self.user_repository.update(
            target_user.uuid,
            {
                "uuid": str(data.user_uuid),
                "password": hashed_password,
            },
        )
        if isinstance(updated_user, common_exceptions.UserNotFoundError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user

        await self.session.commit()


class UpdateUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.Context,
        validator: validators.UpdateUserValidator,
        user_policy: interfaces.UserAuthorizationPolicy,
        logger: common_interfaces.Logger,
    ):
        self.user_context = context
        self.validator = validator
        self.user_repository = user_repository
        self.session = session
        self.policy = user_policy
        self.logger = logger

    async def execute(self, data: dto.UpdateUserInDTO) -> dto.UpdateUserOutDTO:
        """Обновляет пользователя.

        Args:
            data: Структура UpdateUserInDTO.
                - uuid: UUID | None
                - name: str | None
                - email: str | None
                - password: str | None
                - status: str | None
                - role: str | None

        Returns:
            dto.UpdateUserOutDTO: Структура результата.
                - user: entities.User

        Raises:
            common_exceptions.InvalidTokenError: Токен пользователя невалиден.
            common_exceptions.UserNotFoundError: Пользователь не найден.
            exceptions.UserAuthorizationError: Недостаточно прав для обновления пользователя.
            exceptions.CantUpdateError: Обновление нарушает доменные ограничения.
            exceptions.UserValidationError: Входные данные не прошли валидацию.
            common_exceptions.EmailAlreadyExistsError: Пользователь с таким email уже существует.
            common_exceptions.RepositoryError: Ошибка репозитория.
        """
        target_user = None
        current_user = None

        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidTokenError):
            raise current_user_uuid

        if data.uuid is None:
            current_user = await self.user_repository.get_by_uuid(
                current_user_uuid, lock_record=True
            )
            if isinstance(current_user, common_exceptions.UserNotFoundError):
                raise current_user
            if isinstance(current_user, common_exceptions.RepositoryError):
                raise current_user

            target_user = current_user

            auth_error = self.policy.decide_update_user(
                actor=current_user,
                target=target_user,
            )
            if auth_error is not None:
                raise auth_error

        else:
            current_user = await self.user_repository.get_by_uuid(current_user_uuid)
            if isinstance(current_user, common_exceptions.UserNotFoundError):
                raise current_user
            if isinstance(current_user, common_exceptions.RepositoryError):
                raise current_user

            target_user = await self.user_repository.get_by_uuid(
                data.uuid, lock_record=True
            )
            if isinstance(target_user, common_exceptions.UserNotFoundError):
                raise target_user
            if isinstance(target_user, common_exceptions.RepositoryError):
                raise target_user

            auth_error = self.policy.decide_update_user(
                actor=current_user,
                target=target_user,
            )
            if auth_error is not None:
                raise auth_error

        if error := current_user.ensure_update(
            target=target_user,
            change_role=data.role is not None,
            change_status=data.status is not None,
        ):
            raise exceptions.CantUpdateError(error)

        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        updated_user = await self.user_repository.update(
            target_user.uuid, {k: v for k, v in data.__dict__.items() if v is not None}
        )
        if isinstance(updated_user, common_exceptions.UserNotFoundError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.EmailAlreadyExistsError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user

        await self.session.commit()

        await self.logger.info(
            operation="UpdateUser",
            message=f"User {updated_user.uuid} updated by {current_user.uuid}",
        )

        return dto.UpdateUserOutDTO(user=updated_user)
