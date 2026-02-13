from uuid import uuid4
from domain import entities
from application import common_interfaces, common_exceptions
from . import interfaces
from . import validators
from . import dto
from . import exceptions


class CreateUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        context: common_interfaces.UserContext,
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
        
    async def execute(self, data: dto.CreateUserInDTO) -> dto.CreateUserOutDTO | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        current_user_uuid = self.context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
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
            created_at=self.clock.now_date(),
            role=data.role,
        )
        created_user = await self.user_repository.create(new_user)

        if isinstance(created_user, common_exceptions.RepositoryError):
            raise created_user

        await self.session.commit()

        self.logger.info(operation='CreateUser', message=f'User {created_user.uuid} created by {current_user.uuid}')
        
        return dto.CreateUserOutDTO(
            user_uuid=created_user.uuid)



class GetUsersListInteractor:
    def __init__(
        self,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.UserContext,
        project_repository: common_interfaces.ProjectRepository,
        validator: validators.GetUsersListValidator,
        user_policy: interfaces.UserAuthorizationPolicy,
    ):

        self.user_context = context
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.validator = validator
        self.policy = user_policy

    async def execute(self, data: dto.GetUserListInDTO) -> dto.GetUserListOutDTO | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | exceptions.UserAuthorizationError | common_exceptions.RepositoryError:
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid

        current_user = await self.user_repository.get_by_uuid(current_user_uuid)
        if isinstance(current_user, common_exceptions.UserNotFoundError):
            raise current_user
        if isinstance(current_user, common_exceptions.RepositoryError):
            raise current_user

        user_projects = await self.user_repository.get_projects(current_user_uuid)
        if isinstance(user_projects, (common_exceptions.UserNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
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

        projects_uuid = (
            [project.uuid for project in user_projects]
        )

        users = await self.project_repository.get_members(
            projects_uuid=projects_uuid,
            is_active=data.is_active if data.is_active is not None else False,
        )

        if isinstance(users, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise users

        return dto.GetUserListOutDTO(
            users=users
        )

class LoginUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        hash_generator: interfaces.HashVerifier,
        context: common_interfaces.UserContext,
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
        
    async def execute(self, data: dto.LoginUserInDTO) -> dto.LoginUserOutDTO | exceptions.InvalidCredentialsError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
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

        updated_user = await self.user_repository.update(user.uuid, {
            'last_login': self.clock.now_date(),
        })
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user
        
        await self.session.commit()
        
        self.logger.info(operation='LoginUser', message=f'User {user.uuid} logged in')
        
        return dto.LoginUserOutDTO(
            token=self.token_generator.generate(user.uuid),
            user_uuid=user.uuid,
        )

class ResetUserPasswordInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.UserContext,
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
        
    async def execute(self, data: dto.ResetUserPasswordInDTO) -> None | common_exceptions.UserNotFoundError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        target_user = None
        current_user = None
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid
        
        if data.user_uuid is None:
    

            current_user = await self.user_repository.get_by_uuid(current_user_uuid, lock_record=True)
            if isinstance(current_user, common_exceptions.UserNotFoundError):
                raise current_user
            if isinstance(current_user, common_exceptions.RepositoryError):
                raise current_user
        
            target_user = current_user
        
        else:
            target_user = await self.user_repository.get_by_uuid(data.user_uuid, lock_record=True)
            if isinstance(target_user, common_exceptions.UserNotFoundError):
                raise target_user
            if isinstance(target_user, common_exceptions.RepositoryError):
                raise target_user

        auth_error = self.policy.decide_reset_password(
            actor=current_user, # type: ignore
            target=target_user,)
        
        if auth_error is not None:
            raise auth_error

        if error := current_user.ensure_reset_password(target_user): # type: ignore
            raise exceptions.CantResetPasswordError(error)
        
        validation_error = self.validator.validate(data)
        if validation_error is not None:
            raise validation_error

        hashed_password = self.hash_generator.generate(data.new_password)

        updated_user = await self.user_repository.update(
            target_user.uuid, {
                "uuid": str(data.user_uuid),
                "password": hashed_password,
            })
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user
        
        await self.session.commit()

class UpdateUserInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        user_repository: common_interfaces.UserRepository,
        context: common_interfaces.UserContext,
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
        
    async def execute(self, data: dto.UpdateUserInDTO) -> dto.UpdateUserOutDTO | common_exceptions.UserNotFoundError | common_exceptions.EmailAlreadyExistsError | common_exceptions.InvalidToken | common_exceptions.RepositoryError:
        target_user = None
        current_user = None
        
        current_user_uuid = self.user_context.get_current_user_uuid()
        if isinstance(current_user_uuid, common_exceptions.InvalidToken):
            raise current_user_uuid
        
        if data.uuid is None:
            current_user = await self.user_repository.get_by_uuid(current_user_uuid, lock_record=True)
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
            
            target_user = await self.user_repository.get_by_uuid(data.uuid, lock_record=True)
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

        updated_user = await self.user_repository.update(target_user.uuid, {k: v for k, v in data.__dict__.items() if v is not None})
        if isinstance(updated_user, common_exceptions.EmailAlreadyExistsError):
            raise updated_user
        if isinstance(updated_user, common_exceptions.RepositoryError):
            raise updated_user

        await self.session.commit()

        self.logger.info(operation='UpdateUser', message=f'User {updated_user.uuid} updated by {current_user.uuid}')    
        
        return dto.UpdateUserOutDTO(user=updated_user)


