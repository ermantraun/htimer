from typing import Any, Awaitable, Callable, TypeVar, cast
from uuid import UUID
import asyncio
from datetime import date

import sqlalchemy as sq
from sqlalchemy import select, insert,delete, and_
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import psycopg.errors

from application import common_exceptions, common_interfaces
from domain import entities
from config import Config
from . import models

TExc = TypeVar("TExc", bound=Exception)


class _RepositoryDebugMixin:
    _debug_db: bool

    def _init_debug(self, config: Config) -> None:
        self._debug_db = bool(getattr(config.postgres, "debug", False))

    def _exc_details(self, exc: BaseException) -> str:
        orig = getattr(exc, "orig", None)
        if orig is not None:
            return f"{type(exc).__name__}: {exc}; orig={type(orig).__name__}: {orig}"
        return f"{type(exc).__name__}: {exc}"

    def _build_error(
        self,
        error_cls: type[TExc],
        message: str,
        exc: BaseException | None = None,
    ) -> TExc:
        if self._debug_db and exc is not None:
            return error_cls(f"{message}. Details: {self._exc_details(exc)}")
        return error_cls(message)

    def _enrich_error(self, exc: TExc) -> TExc:
        if not self._debug_db:
            return exc

        if "Details:" in str(exc):
            return exc

        cause = exc.__cause__
        if cause is None:
            return exc

        return type(exc)(f"{exc}. Details: {self._exc_details(cause)}")

async def _execute_idempotent(
        session: AsyncSession,
        idempotent_retries: int,
        base_backoff: float,
        operation: Callable[[], Awaitable[Any]],
        *,
        error_message: str,
        exception: type[Exception]
    ):
        attempt = 0
        while True:
            try:
                return await operation()
            except (OperationalError, DBAPIError) as exc:
                if isinstance(exc, IntegrityError):
                    raise
                await session.rollback()
                if attempt >= idempotent_retries:
                    raise exception(error_message) from exc

                attempt += 1
                await asyncio.sleep(base_backoff * (attempt + 1))


async def _execute_statement_idempotent(
    session: AsyncSession,
    idempotent_retries: int,
    base_backoff: float,
    statement: Any,
    *,
    error_message: str,
    exception: type[Exception],
):
    async def _op() -> Any:
        return await session.execute(statement)

    return await _execute_idempotent(
        session,
        idempotent_retries,
        base_backoff,
        _op,
        error_message=error_message,
        exception=exception,
    )

class UserRepository(_RepositoryDebugMixin, common_interfaces.UserRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)

    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.RepositoryError:
        try:

            new_user = models.User(
                uuid=data.uuid,
                name=data.name,
                email=data.email,
                password_hash=data.password_hash,
                creator_uuid=data.creator.uuid if getattr(data, "creator", None) else None,
                role=self.map_role_to_model(data.role),
                status=self.map_status_to_model(data.status),
                created_at=data.created_at,
                last_login=data.last_login,
            )

            self.session.add(new_user)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось создать пользователя",
                exception=common_exceptions.UserRepositoryError
            )

            loaded_user = await self._get_user_model(new_user.uuid)
            if loaded_user is None:
                return self._build_error(common_exceptions.UserRepositoryError, "Не удалось создать пользователя")

            return self.map_user_to_entity(loaded_user)
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.EmailAlreadyExistsError(
                "Пользователь с таким email уже существует"
            )
        except common_exceptions.UserRepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось создать пользователя", exc)

    async def update(self, user_uuid: UUID, data: dict[str, Any]) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try:
            user_model = await self._get_user_model(user_uuid, lock_record=True)
            
            if user_model is None:
                return common_exceptions.UserNotFoundError("Пользователь не найден")

            self._apply_user_updates(user_model, data)

            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось обновить пользователя",
                exception=common_exceptions.UserRepositoryError
            )

            loaded_user = await self._get_user_model(user_uuid)
            if loaded_user is None:
                return common_exceptions.UserNotFoundError("Пользователь не найден")

            return self.map_user_to_entity(loaded_user)
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.EmailAlreadyExistsError(
                "Пользователь с таким email уже существует"
            )
        except common_exceptions.UserRepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось обновить пользователя", exc)

    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try:
            async def _op():
                return await self._fetch_user_by_email(email)
            
            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff,
                _op,
                error_message="Не удалось получить пользователя по email",
                exception=common_exceptions.UserRepositoryError
            )
        except common_exceptions.UserRepositoryError as exc:
            return self._enrich_error(exc)
        
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось получить пользователя по email", exc)

    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try:
            async def _op():
                return await self._fetch_user_by_uuid(user_uuid, lock_record=lock_record)
            
            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff,
                _op,
                error_message="Не удалось получить пользователя по uuid",
                exception=common_exceptions.UserRepositoryError
            )
            
        
        except common_exceptions.UserRepositoryError as exc:
            return self._enrich_error(exc)

        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось получить пользователя по uuid", exc)

    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                    select(models.User)
                    .options(selectinload(models.User.creator))
                    .where(models.User.uuid.in_(users_uuid))
                )
            async def _op():

                
                result = await self.session.execute(stmt)
                result = result.scalars().all()

                return result
            
            users = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить список пользователей", exception=common_exceptions.UserRepositoryError)

            users = [self.map_user_to_entity(user) for user in users]
            
            if len(users) != len(users_uuid):
                return common_exceptions.UserNotFoundError("Один или несколько пользователей не найдены")

            
            return users
        
        except common_exceptions.UserRepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось получить список пользователей", exc)
        
        
    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            async def _op() -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError:
                if user_uuid is None:
                    return []

                user_model = await self._get_user_model(user_uuid)
                if user_model is None:
                    return common_exceptions.UserNotFoundError("Пользователь не найден")

                owned_stmt = select(models.Project).where(
                    models.Project.creator_uuid == user_uuid
                ).options(selectinload(models.Project.creator))
                member_stmt = (
                    select(models.Project)
                    .options(selectinload(models.Project.creator))
                    .join(models.MemberShip, models.MemberShip.project_uuid == models.Project.uuid)
                    .where(models.MemberShip.user_uuid == user_uuid)
                )

                owned_projects_result = await self.session.execute(owned_stmt)
                member_projects_result = await self.session.execute(member_stmt)

                projects_models = {project.uuid: project for project in owned_projects_result.scalars().all()}
                for proj in member_projects_result.scalars().all():
                    projects_models.setdefault(proj.uuid, proj)

                return [ProjectRepository.map_project_to_entity(project) for project in projects_models.values()]

            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить проекты пользователя", exception=common_exceptions.UserRepositoryError)
        except common_exceptions.UserRepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.UserRepositoryError, "Не удалось получить проекты пользователя", exc)
    
    def _apply_user_updates(self, user_model: models.User, data: dict[str, Any]) -> None:
        if "name" in data:
            user_model.name = data["name"]
        if "email" in data:
            user_model.email = data["email"]
        if "password" in data:
            user_model.password_hash = data["password"]
        if "password_hash" in data:
            user_model.password_hash = data["password_hash"]
        if "role" in data:
            user_model.role = self.map_role_to_model(data["role"])
        if "status" in data:
            user_model.status = self.map_status_to_model(data["status"])
        if "last_login" in data:
            user_model.last_login = data["last_login"]

    async def _fetch_user_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError:
        stmt = (
            select(models.User)
            .options(selectinload(models.User.creator))
            .where(models.User.email == email)
        )
        result = await _execute_statement_idempotent(
            self.session,
            self._idempotent_retries,
            self._base_backoff,
            stmt,
            error_message="Не удалось получить пользователя по email",
            exception=common_exceptions.UserRepositoryError,
        )
        user = result.scalar_one_or_none()
        if user is None:
            return common_exceptions.UserNotFoundError("Пользователь не найден")
        return self.map_user_to_entity(user)

    async def _fetch_user_by_uuid(
        self, user_uuid: UUID, *, lock_record: bool = False
    ) -> entities.User | common_exceptions.UserNotFoundError:
        user_model = await self._get_user_model(user_uuid, lock_record=lock_record)
        if user_model is None:
            return common_exceptions.UserNotFoundError("Пользователь не найден")
        return self.map_user_to_entity(user_model)

    async def _get_user_model(
        self, user_uuid: UUID, *, lock_record: bool = False
    ) -> models.User | None:
        stmt = (
                select(models.User)
            .options(selectinload(models.User.creator))
                .where(models.User.uuid == user_uuid)
            )
        if lock_record:
            stmt = stmt.with_for_update()

        def _op():
            return self.session.execute(stmt)
        result = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить пользователя по uuid", exception=common_exceptions.UserRepositoryError)
        return result.scalar_one_or_none()

    @classmethod
    def map_user_to_entity(cls, user_model: models.User, creators_level: int = 1) -> entities.User:
        
        if creators_level == 0 or user_model.creator_uuid is None:
            creator_entity: entities.User | None = None
        else:
            creator_entity = (
                cls.map_user_to_entity(user_model.creator, creators_level=creators_level - 1)
                if user_model.creator is not None
                else None
            )

        return entities.User(
            uuid=user_model.uuid,
            name=user_model.name,
            email=user_model.email,
            password_hash=user_model.password_hash,
            creator=cast(entities.User, creator_entity),
            role=cls.map_role_to_domain(user_model.role),
            status=cls.map_status_to_domain(user_model.status),
            created_at=user_model.created_at,
            last_login=user_model.last_login,
        )



    @classmethod
    def map_role_to_domain(cls, role: models.UserRole) -> entities.UserRole:
        return entities.UserRole.ADMIN if role is models.UserRole.ADMIN else entities.UserRole.EXECUTOR

    @classmethod
    def map_role_to_model(cls, role: entities.UserRole) -> models.UserRole:
        return models.UserRole.ADMIN if role is entities.UserRole.ADMIN else models.UserRole.USER

    @classmethod
    def map_status_to_domain(cls, status: models.UserStatus) -> entities.UserStatus:
        mapping = {
            models.UserStatus.ACTIVE: entities.UserStatus.ACTIVE,
            models.UserStatus.BLOCKED: entities.UserStatus.BLOCKED,
            models.UserStatus.ARCHIVED: entities.UserStatus.ARCHIVED,
        }
        return mapping[status]

    @classmethod
    def map_status_to_model(cls, status: entities.UserStatus) -> models.UserStatus:
        mapping = {
            entities.UserStatus.ACTIVE: models.UserStatus.ACTIVE,
            entities.UserStatus.BLOCKED: models.UserStatus.BLOCKED,
            entities.UserStatus.ARCHIVED: models.UserStatus.ARCHIVED,
        }
        return mapping[status]



class ProjectRepository(_RepositoryDebugMixin, common_interfaces.ProjectRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        
    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try: 
            project = models.Project(
                uuid=data.uuid,
                name=data.name,
                description=data.description,
                creator_uuid=data.creator.uuid,
                start_date=data.start_date,
                end_date=data.end_date,
                status=self.map_project_status_to_model(data.status),
                created_at=data.created_at,
            )
            
            self.session.add(project)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff,
                                    _op,
                                    error_message="Не удалось создать проект",
                                    exception=common_exceptions.ProjectRepositoryError
            )

            loaded_project = await self._get_project_model(project.uuid)
            if loaded_project is None:
                return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось создать проект")

            return self.map_project_to_entity(loaded_project)
        
        except IntegrityError as exc:
            await self.session.rollback()
            if isinstance(exc.orig, psycopg.errors.ForeignKeyViolation):
                return common_exceptions.UserNotFoundError("Пользователь не найден")
            elif isinstance(exc.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.UserAlreadyHasProjectError("Проект с таким именем уже существует")
            else:
                return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось создать проект", exc)
        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)
        
        
        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось создать проект", exc)
        
    async def update(self, project_uuid: UUID, data: dict[str, Any]) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.RepositoryError:
        try:
            project_model = await self._get_project_model(project_uuid, lock_record=True)
            
            if project_model is None:
                return common_exceptions.ProjectNotFoundError("Проект не найден")

            self._apply_project_updates(project_model, data)

            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось обновить проект",
                exception=common_exceptions.ProjectRepositoryError
            )

            loaded_project = await self._get_project_model(project_model.uuid)
            if loaded_project is None:
                return common_exceptions.ProjectNotFoundError("Проект не найден")

            return self.map_project_to_entity(loaded_project)
        
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.UserAlreadyHasProjectError("Проект с таким именем уже существует")

        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)

        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось обновить проект", exc)
    
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        
        try: 
            project = await self._get_project_model(project_uuid, lock_record)
            
            if project is None: 
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            return self.map_project_to_entity(project)

        except common_exceptions.ProjectRepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось получить проект", exc)
            
        
    async def get_by_name(self, user_uuid: UUID, project_name: str) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Project)
                .options(selectinload(models.Project.creator))
                .join(models.User, models.Project.creator_uuid == models.User.uuid)  # 2 аргумента: таблица и onclause
                .where(and_(models.Project.name == project_name, models.User.uuid == user_uuid))
                .limit(1)
            )

            async def _op():
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()

            project_model = await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось получить проект",
                exception=common_exceptions.ProjectRepositoryError,
            )

            if project_model is None:
                return common_exceptions.ProjectNotFoundError("Проект не найден")

            return self.map_project_to_entity(project_model) 
        except common_exceptions.ProjectRepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось получить проект", exc)
    
    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | common_exceptions.RepositoryError:
        try: 
            
            members_values: list[dict[str, Any]] = [
                {
                    "uuid": membership.uuid,
                    "project_uuid": membership.project.uuid,
                    "user_uuid": membership.user.uuid,
                    "assigned_by_uuid": membership.assigned_by.uuid,
                    "joined_at": membership.joined_at,
                }
                for membership in members
            ]

            insert_members_stmt = insert(models.MemberShip).values(members_values)
            
            async def _op() -> None:
                await self.session.execute(insert_members_stmt)
            
            await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось добавить пользователей",
                exception=common_exceptions.ProjectRepositoryError,
            )
        

            return members
        
        except IntegrityError as exc:
            await self.session.rollback()
            if isinstance(exc.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(exc.orig.diag, "constraint_name", None)
                if constraint_name:
                    if "memberships_project_uuid_fkey" in constraint_name:
                        return common_exceptions.ProjectNotFoundError("Проект не найден")
                    elif "memberships_user_uuid_fkey" in constraint_name:
                        return common_exceptions.UserNotFoundError("Пользователь не найден")
            elif isinstance(exc.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.UserAlreadyProjectMemberError("Пользователь уже является участником проекта")
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось добавить пользователей", exc)
        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.ProjectRepositoryError, "Не удалось добавить пользователей", exc)

        
    
    async def remove_members(self, project_uuid: UUID, members_uuids: list[UUID]) -> None | common_exceptions.MemberNotFound | common_exceptions.RepositoryError:
        
        try: 
            exist_stmt = select(sq.func.count(models.MemberShip.user_uuid)).where(sq.and_(models.MemberShip.project_uuid == project_uuid, models.MemberShip.user_uuid.in_(members_uuids)))
            
            async def _op(): #type: ignore
                result = await self.session.execute(exist_stmt)
                return result.scalar()
            
            result = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось удалить участников проекта', exception=common_exceptions.RepositoryError )
        
            if result == 0:
                return common_exceptions.MemberNotFound()
            
            delete_stmt = delete(models.MemberShip).where(sq.and_(models.MemberShip.project_uuid == project_uuid, models.MemberShip.user_uuid.in_(members_uuids)))

            async def _op():
                await self.session.execute(delete_stmt)
            
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось удалить участников проекта', exception=common_exceptions.RepositoryError )
                        
        except common_exceptions.RepositoryError as exc:
            await self.session.rollback()
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось удалить участников проекта", exc)
    
    async def get_members(self, projects_uuid: list[UUID], is_active: bool = True) -> list[entities.User] | common_exceptions.RepositoryError | common_exceptions.ProjectNotFoundError:
        try:
            
            project_exist_stmt = select(sq.func.count(models.Project.uuid)).where(models.Project.uuid.in_(projects_uuid))
            
            async def _op(): #type: ignore
                result = await self.session.execute(project_exist_stmt)
                return result.scalar_one_or_none()
            
            project_count = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось проверить существование проекта', exception=common_exceptions.RepositoryError )
            if project_count != len(projects_uuid):
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            stmt = select(models.MemberShip).join(models.User, onclause=models.MemberShip.user_uuid == models.User.uuid).where(models.MemberShip.project_uuid.in_(projects_uuid))
            stmt = stmt.options(selectinload(models.MemberShip.user).selectinload(models.User.creator))
            if is_active:
                stmt = stmt.where(models.User.status == models.UserStatus.ACTIVE)
                
            async def _op():
                return await self.session.execute(stmt)
            result = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить участников проекта', exception=common_exceptions.RepositoryError )
            members_models = result.scalars().all()
            return [
                UserRepository.map_user_to_entity(member.user)
                for member in members_models
            ]
        except common_exceptions.RepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить участников проекта", exc)
    
    async def get_current_subscription(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            project_exist_stmt = select(sq.func.count(models.Project.uuid)).where(models.Project.uuid == project_uuid)
            
            async def _op(): #type: ignore
                result = await self.session.execute(project_exist_stmt)
                return result.scalar_one_or_none()
            
            project_count = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось проверить существование проекта', exception=common_exceptions.RepositoryError )
            if project_count == 0:
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            stmt = select(models.Subscription).where(models.Subscription.project_uuid == project_uuid).order_by(models.Subscription.end_date.desc()).limit(1)
            stmt = stmt.options(
                selectinload(models.Subscription.project).selectinload(models.Project.creator)
            )

            async def _op():
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
            
            subscription_model = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить подписку проекта', exception=common_exceptions.RepositoryError )
            
            if subscription_model is None or subscription_model.end_date < date.today():
                return common_exceptions.SubscriptionNotFoundError("Подписка не найдена")
            
            return SubscriptionRepository.map_subscription_to_entity(subscription_model)
        except common_exceptions.RepositoryError as exc:
            return self._enrich_error(exc)
        except (TimeoutError, DBAPIError) as exc:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить подписку проекта", exc)
    
    @classmethod
    def map_members_entities_to_models(cls, memberships: list[entities.MemberShip]) -> list[models.MemberShip]:
        return [
            models.MemberShip(
                uuid=membership.uuid,
                project_uuid=membership.project.uuid,
                user_uuid=membership.user.uuid,
                assigned_by_uuid=membership.assigned_by.uuid,
                joined_at=membership.joined_at
            ) for membership in memberships
        ]
        
    @classmethod
    def map_members_models_to_entities(cls, memberships: list[models.MemberShip]) -> list[entities.MemberShip]:
        return [
            entities.MemberShip(
                uuid=membership.uuid,
                project=ProjectRepository.map_project_to_entity(membership.project),
                user=UserRepository.map_user_to_entity(membership.user),
                assigned_by=UserRepository.map_user_to_entity(membership.assigned_by_user),
                joined_at=membership.joined_at,
            )
            for membership in memberships
        ]
    
    @classmethod
    def map_project_to_model(cls, entitie: entities.Project) -> models.Project:
        return models.Project(
            uuid=entitie.uuid,
            name=entitie.name,
            description=entitie.description,
            creator_uuid=entitie.creator.uuid,
            start_date=entitie.start_date,
            end_date=entitie.end_date,
            status=cls.map_project_status_to_model(entitie.status),
            created_at=entitie.created_at,
        )

    @classmethod
    def map_project_model_to_entity(cls, model: models.Project) -> entities.Project:
        return entities.Project(
            uuid=model.uuid,
            name=model.name,
            description=model.description,
            creator=UserRepository.map_user_to_entity(model.creator),
            created_at=model.created_at,
            status=cls.map_project_status_to_domain(model.status),
            start_date=model.start_date,
            end_date=model.end_date,
        )
    
    async def _get_project_model(self, project_uuid: UUID, lock_record: bool = False) -> models.Project | None:
        stmt = (
            select(models.Project)
            .options(selectinload(models.Project.creator))
            .where(models.Project.uuid == project_uuid)
        )
        if lock_record:
            stmt = stmt.with_for_update()

        async def _op() -> models.Project | None:
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить проект по uuid", exception=common_exceptions.ProjectRepositoryError)
    
    def _apply_project_updates(self, project_model: models.Project, data: dict[str, Any]) -> None:
        if "name" in data:
            project_model.name = data["name"]
        if "description" in data:
            project_model.description = data["description"]
        if "status" in data:
            project_model.status = self.map_project_status_to_model(data["status"])
        if "start_date" in data:
            project_model.start_date = data["start_date"]
        if "end_date" in data:
            project_model.end_date = data["end_date"]
    
    @classmethod
    def map_project_status_to_model(cls, status: entities.ProjectStatus) -> models.ProjectStatus:
        mapping = {
            entities.ProjectStatus.ACTIVE: models.ProjectStatus.ACTIVE,
            entities.ProjectStatus.ARCHIVED: models.ProjectStatus.ARCHIVED,
            entities.ProjectStatus.BLOCKED: models.ProjectStatus.BLOCKED,
            entities.ProjectStatus.COMPLETED: models.ProjectStatus.COMPLETED,
        }
        return mapping[status]

    @classmethod
    def map_project_status_to_domain(cls, status: models.ProjectStatus) -> entities.ProjectStatus:
        mapping = {
            models.ProjectStatus.ACTIVE: entities.ProjectStatus.ACTIVE,
            models.ProjectStatus.ARCHIVED: entities.ProjectStatus.ARCHIVED,
            models.ProjectStatus.BLOCKED: entities.ProjectStatus.BLOCKED,
            models.ProjectStatus.COMPLETED: entities.ProjectStatus.COMPLETED,
        }
        return mapping[status]

    @classmethod
    def map_project_to_entity(cls, project_model: models.Project) -> entities.Project:
        return entities.Project(
            uuid=project_model.uuid,
            name=project_model.name,
            description=project_model.description,
            creator=UserRepository.map_user_to_entity(project_model.creator),
            created_at=project_model.created_at,
            status=cls.map_project_status_to_domain(project_model.status),
            start_date=project_model.start_date,
            end_date=project_model.end_date,
        )



class StageRepository(_RepositoryDebugMixin, common_interfaces.StageRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        

    async def create(self, data: entities.Stage) -> entities.Stage | common_exceptions.StageAlreadyExistsError | common_exceptions.ParentStageAlreadyHasMainSubStageError | common_exceptions.UserNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        
        try: 
            stage = self.map_entity_to_stage(data)
            
            self.session.add(stage)
            
            async def _op():
                return await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось создать этап', exception=common_exceptions.RepositoryError)

            loaded_stage_stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.uuid == data.uuid)
            )
            loaded_stage_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_stage_stmt,
                error_message="Не удалось создать этап",
                exception=common_exceptions.RepositoryError,
            )
            loaded_stage = loaded_stage_result.scalar_one_or_none()
            if loaded_stage is None:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать этап")

            return self.map_stage_to_entity(loaded_stage)
        
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name and "stages_project_uuid_fkey" in constraint_name:
                    return common_exceptions.ProjectNotFoundError("Проект не найден")
                if constraint_name and "stages_creator_uuid_fkey" in constraint_name:
                    return common_exceptions.UserNotFoundError("Пользователь не найден")
            if isinstance(e.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.StageAlreadyExistsError("Этап с таким именем уже существует")
            if isinstance(e.orig, psycopg.errors.CheckViolation):
                return common_exceptions.ParentStageAlreadyHasMainSubStageError("Главный подэтап уже существует")
            constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)

            if constraint_name:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать этап", e)

            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать этап", e)
            
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
    
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать этап", e)
    
    async def get_list(self, project_uuid: UUID) -> list[entities.Stage] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            project_exist_stmt = select(sq.exists().where(models.Project.uuid == project_uuid))
            async def _op():
                result = await self.session.execute(project_exist_stmt)
                return result.scalar_one_or_none()
            
            project_exist = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось проверить существование проекта', exception=common_exceptions.RepositoryError )
            if not project_exist:
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            stages_stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.project_uuid == project_uuid)
            )
            async def _op_stages():
                result = await self.session.execute(stages_stmt)
                return result.scalars().all()
            
            stages = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op_stages, error_message='Не удалось получить этапы проекта', exception=common_exceptions.RepositoryError )
            return [self.map_stage_to_entity(stage) for stage in stages]
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить этапы проекта", e)
    
    async def update(self, stage_uuid: UUID, data: dict[str, Any]) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.uuid == stage_uuid)
            )
            result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                stmt,
                error_message="Не удалось получить этап",
                exception=common_exceptions.RepositoryError,
            )
            stage = result.scalar_one_or_none()
            if stage is None:
                return common_exceptions.StageNotFoundError("Этап не найден")
            for key, value in data.items():
                setattr(stage, key, value)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось обновить этап', exception=common_exceptions.RepositoryError )

            loaded_stage_stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.uuid == stage_uuid)
            )
            loaded_stage_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_stage_stmt,
                error_message="Не удалось обновить этап",
                exception=common_exceptions.RepositoryError,
            )
            loaded_stage = loaded_stage_result.scalar_one_or_none()
            if loaded_stage is None:
                return common_exceptions.StageNotFoundError("Этап не найден")

            return self.map_stage_to_entity(loaded_stage)
        
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить этап", e)
    
    async def delete(self, stage_uuid: UUID) -> None | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        try:
            stage = await self.session.get(models.Stage, stage_uuid)
            if stage is None:
                return common_exceptions.StageNotFoundError("Этап не найден")
            
            stmt = delete(models.Stage).where(models.Stage.uuid == stage_uuid)
            
            async def _op():
                await self.session.execute(stmt)
                
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось удалить этап', exception=common_exceptions.RepositoryError )
            
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
            
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось удалить этап", e)
    
    async def get_by_name(self, project_uuid: UUID, stage_name: str, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.project_uuid == project_uuid, models.Stage.name == stage_name)
            )
            
            async def _op():
                return await self.session.execute(stmt)
            
            result = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить этап', exception=common_exceptions.RepositoryError )
            
            stage = result.scalar_one_or_none()
            if stage is None:
                return common_exceptions.StageNotFoundError("Этап не найден")
            return self.map_stage_to_entity(stage)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить этап", e)
    
    async def get_by_uuid(self, stage_uuid: UUID, lock_record: bool = False) -> entities.Stage | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Stage)
                .options(
                    selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Stage.parent),
                    selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Stage.uuid == stage_uuid)
            )
            
            if lock_record:
                stmt = stmt.with_for_update()
            
            async def _op():
                return await self.session.execute(stmt)
            
            
            
            result = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить этап', exception=common_exceptions.RepositoryError )
            stage = result.scalar_one_or_none()
            if stage is None:
                return common_exceptions.StageNotFoundError("Этап не найден")
            return self.map_stage_to_entity(stage)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить этап", e)
    
    @classmethod
    def map_stage_status_to_model(cls, status: entities.StageStatus) -> models.StageStatus:
        mapping = {
            entities.StageStatus.ACTIVE: models.StageStatus.ACTIVE,
            entities.StageStatus.ARCHIVED: models.StageStatus.ARCHIVED,
            entities.StageStatus.COMPLETED: models.StageStatus.COMPLETED,
        }
        return mapping[status]
    
    @classmethod
    def map_stage_status_to_domain(cls, status: models.StageStatus) -> entities.StageStatus:
        mapping = {
            models.StageStatus.ACTIVE: entities.StageStatus.ACTIVE,
            models.StageStatus.ARCHIVED: entities.StageStatus.ARCHIVED,
            models.StageStatus.COMPLETED: entities.StageStatus.COMPLETED,
        }
        return mapping[status]
    
    @classmethod
    def map_entity_to_stage(cls, stage_entity: entities.Stage) -> models.Stage:
        return models.Stage(
            uuid=stage_entity.uuid,
            name=stage_entity.name,
            creator_uuid=stage_entity.creator.uuid,
            project_uuid=stage_entity.project.uuid,
            parent_uuid=stage_entity.parent.uuid if stage_entity.parent is not None else None,
            description=stage_entity.description,
            created_at=stage_entity.created_at,
            main_path=stage_entity.main_path,
            status=cls.map_stage_status_to_model(stage_entity.status)
        )
    
    @classmethod
    def map_stage_to_entity(cls, stage_model: models.Stage, parents_level: int = 1) -> entities.Stage:
        if parents_level == 0 or stage_model.parent_uuid is None:
            parent_entity: entities.Stage | None = None
        else:
            parent_entity = (
                cls.map_stage_to_entity(stage_model.parent, parents_level=parents_level - 1)
                if stage_model.parent is not None
                else None
            )
        return entities.Stage(
            uuid=stage_model.uuid,
            name=stage_model.name,
            creator=UserRepository.map_user_to_entity(stage_model.creator),
            project=ProjectRepository.map_project_to_entity(stage_model.project),
            description=stage_model.description,
            created_at=stage_model.created_at,
            parent=parent_entity,
            main_path=stage_model.main_path,
            status=cls.map_stage_status_to_domain(stage_model.status)
        )
        

class DailyLogRepository(_RepositoryDebugMixin, common_interfaces.DailyLogRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        
        
    async def create(self, data: entities.DailyLog) -> entities.DailyLog | common_exceptions.DailyLogAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.StageNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try: 
            daily_log = self.map_entity_to_daily_log(data)
            self.session.add(daily_log)
            
            async def _op():
                return await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось создать ежедневный отчет', exception=common_exceptions.RepositoryError)

            loaded_daily_log_stmt = (
                select(models.DailyLog)
                .options(
                    selectinload(models.DailyLog.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.DailyLog.uuid == data.uuid)
            )
            loaded_daily_log_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_daily_log_stmt,
                error_message="Не удалось создать ежедневный отчет",
                exception=common_exceptions.RepositoryError,
            )
            loaded_daily_log = loaded_daily_log_result.scalar_one_or_none()
            if loaded_daily_log is None:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать ежедневный отчет")

            return self.map_daily_log_to_entity(loaded_daily_log)
            
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name and "daily_logs_substage_uuid_fkey" in constraint_name:
                    return common_exceptions.StageNotFoundError("Этап не найден")
                if constraint_name and "daily_logs_creator_uuid_fkey" in constraint_name:
                    return common_exceptions.UserNotFoundError("Пользователь не найден")
                if constraint_name and "daily_logs_project_uuid_fkey" in constraint_name:
                    return common_exceptions.ProjectNotFoundError("Проект не найден")
            if isinstance(e.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.DailyLogAlreadyExistsError("Ежедневный отчет уже существует")
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать ежедневный отчет", e)
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать ежедневный отчет", e)
        
    async def update(self, day_uuid: UUID, data: dict[str, Any]) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.DailyLog)
                .options(
                    selectinload(models.DailyLog.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.DailyLog.uuid == day_uuid)
            )
            result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                stmt,
                error_message="Не удалось получить ежедневный отчет",
                exception=common_exceptions.RepositoryError,
            )
            daily_log = result.scalar_one_or_none()
            if daily_log is None:
                return common_exceptions.DailyLogNotFoundError("Ежедневный отчет не найден")
            for key, value in data.items():
                setattr(daily_log, key, value)
            
            async def _op():
                await self.session.flush()
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось обновить ежедневный отчет', exception=common_exceptions.RepositoryError )

            loaded_daily_log_stmt = (
                select(models.DailyLog)
                .options(
                    selectinload(models.DailyLog.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.DailyLog.uuid == day_uuid)
            )
            loaded_daily_log_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_daily_log_stmt,
                error_message="Не удалось обновить ежедневный отчет",
                exception=common_exceptions.RepositoryError,
            )
            loaded_daily_log = loaded_daily_log_result.scalar_one_or_none()
            if loaded_daily_log is None:
                return common_exceptions.DailyLogNotFoundError("Ежедневный отчет не найден")

            return self.map_daily_log_to_entity(loaded_daily_log)
        
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить ежедневный отчет", e)
    
    async def get_by_uuid(self, day_uuid: UUID, lock_record: bool = False) -> entities.DailyLog | common_exceptions.DailyLogNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.DailyLog)
                .options(
                    selectinload(models.DailyLog.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.DailyLog.uuid == day_uuid)
            )
            
            if lock_record:
                stmt = stmt.with_for_update()
                
            async def _op():
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
            
            daily_log = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить ежедневный отчет', exception=common_exceptions.RepositoryError )
            if daily_log is None:
                return common_exceptions.DailyLogNotFoundError("Ежедневный отчет не найден")
            return self.map_daily_log_to_entity(daily_log)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить ежедневный отчет", e)
    
    async def get_list(self, project_uuid: UUID, date: date, draft: bool = False) -> list[entities.DailyLog] | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            project_exist_stmt = select(sq.exists().where(models.Project.uuid == project_uuid))
            async def _op(): #type: ignore
                result = await self.session.execute(project_exist_stmt)
                return result.scalar_one_or_none()
            
            project_exist = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось проверить существование проекта', exception=common_exceptions.RepositoryError )
            if not project_exist:
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            daily_log_list_stmt = (
                select(models.DailyLog)
                .options(
                    selectinload(models.DailyLog.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.DailyLog.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .join(models.Project)
                .where(and_(models.DailyLog.project_uuid == models.Project.uuid, models.DailyLog.created_at == date))
            )

            if draft:
                daily_log_list_stmt = daily_log_list_stmt.where(models.DailyLog.draft == draft)

            async def _op():
                result = await self.session.execute(daily_log_list_stmt)
                return result.scalars().all()
            
            daily_logs = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить ежедневные отчеты проекта', exception=common_exceptions.RepositoryError )
            return [self.map_daily_log_to_entity(daily_log) for daily_log in daily_logs]

        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить ежедневные отчеты проекта", e)

    @classmethod    
    def map_daily_log_to_entity(cls, daily_log_model: models.DailyLog) -> entities.DailyLog:
        substage_entity = (
            StageRepository.map_stage_to_entity(daily_log_model.substage)
            if daily_log_model.substage is not None
            else None
        )
        return entities.DailyLog(
            uuid=daily_log_model.uuid,
            substage=substage_entity,
            creator=UserRepository.map_user_to_entity(daily_log_model.creator),
            project=ProjectRepository.map_project_to_entity(daily_log_model.project),
            hours_spent=daily_log_model.hours_spent,
            description=daily_log_model.description,
            created_at=daily_log_model.created_at,
            updated_at=daily_log_model.updated_at,
            draft=daily_log_model.draft,
            
        )
        
    @classmethod
    def map_entity_to_daily_log(cls, daily_log_entity: entities.DailyLog) -> models.DailyLog:
        return models.DailyLog(
            uuid=daily_log_entity.uuid,
            substage_uuid=daily_log_entity.substage.uuid if daily_log_entity.substage is not None else None,
            creator_uuid=daily_log_entity.creator.uuid,
            project_uuid=daily_log_entity.project.uuid,
            hours_spent=daily_log_entity.hours_spent,
            description=daily_log_entity.description,
            created_at=daily_log_entity.created_at,
            updated_at=daily_log_entity.updated_at,
            draft=daily_log_entity.draft,
        )


class TaskRepository(_RepositoryDebugMixin, common_interfaces.TaskRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        
    async def create(self, data: entities.Task) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.StageNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.RepositoryError:
        try:
            task = self.map_entity_to_task(data)
            
            self.session.add(task)
            
            async def _op():
                return await self.session.flush()
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось создать задачу', exception=common_exceptions.RepositoryError)

            loaded_task_stmt = (
                select(models.Task)
                .options(
                    selectinload(models.Task.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Task.uuid == data.uuid)
            )
            loaded_task_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_task_stmt,
                error_message="Не удалось создать задачу",
                exception=common_exceptions.RepositoryError,
            )
            loaded_task = loaded_task_result.scalar_one_or_none()
            if loaded_task is None:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать задачу")

            return self.map_task_to_entity(loaded_task)
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name and "tasks_substage_uuid_fkey" in constraint_name:
                    return common_exceptions.StageNotFoundError("Этап не найден")
                if constraint_name and "tasks_creator_uuid_fkey" in constraint_name:
                    return common_exceptions.UserNotFoundError("Пользователь не найден")
            if isinstance(e.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.TaskAlreadyExistsError("Задача с таким именем уже существует")
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать задачу", e)
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать задачу", e)
    
    async def get_by_uuid(self, task_uuid: UUID, lock_record: bool = False) -> entities.Task | common_exceptions.TaskAlreadyExistsError | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Task)
                .options(
                    selectinload(models.Task.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Task.uuid == task_uuid)
            )
            
            if lock_record:
                stmt = stmt.with_for_update()
            
            async def _op():
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
            
            task_model = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить задачу', exception=common_exceptions.RepositoryError )
            if task_model is None:
                return common_exceptions.TaskNotFoundError("Задача не найдена")
            return self.map_task_to_entity(task_model)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить задачу", e)
        
    async def update(self, task_uuid: UUID, data: dict[str, Any]) -> entities.Task | common_exceptions.TaskNotFoundError | common_exceptions.TaskAlreadyExistsError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Task)
                .options(
                    selectinload(models.Task.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Task.uuid == task_uuid)
            )
            result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                stmt,
                error_message="Не удалось получить задачу",
                exception=common_exceptions.RepositoryError,
            )
            task = result.scalar_one_or_none()
            if task is None:
                return common_exceptions.TaskNotFoundError("Задача не найдена")
            for key, value in data.items():
                setattr(task, key, value)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось обновить задачу', exception=common_exceptions.RepositoryError )

            loaded_task_stmt = (
                select(models.Task)
                .options(
                    selectinload(models.Task.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Task.uuid == task_uuid)
            )
            loaded_task_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_task_stmt,
                error_message="Не удалось обновить задачу",
                exception=common_exceptions.RepositoryError,
            )
            loaded_task = loaded_task_result.scalar_one_or_none()
            if loaded_task is None:
                return common_exceptions.TaskNotFoundError("Задача не найдена")

            return self.map_task_to_entity(loaded_task)
        
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.TaskAlreadyExistsError("Задача с таким именем уже существует")
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить задачу", e)
        
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить задачу", e)
        
    async def delete(self, task_uuid: UUID) -> None | common_exceptions.TaskNotFoundError | common_exceptions.RepositoryError:
        try:
            task = await self.session.get(models.Task, task_uuid)
            if task is None:
                return common_exceptions.TaskNotFoundError("Задача не найдена")
            
            stmt = delete(models.Task).where(models.Task.uuid == task_uuid)
            
            async def _op():
                await self.session.execute(stmt)
                
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось удалить задачу', exception=common_exceptions.RepositoryError )
            
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
            
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось удалить задачу", e)
        
    async def get_list(self, substage_uuid: UUID) -> list[entities.Task] | common_exceptions.StageNotFoundError | common_exceptions.RepositoryError:
        try:
            stage_exist_stmt = select(sq.exists().where(models.Stage.uuid == substage_uuid))
            async def _op(): # type: ignore
                result = await self.session.execute(stage_exist_stmt)
                return result.scalar_one_or_none()
            
            stage_exist = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось проверить существование этапа', exception=common_exceptions.RepositoryError )
            if not stage_exist:
                return common_exceptions.StageNotFoundError("Этап не найден")
            
            stmt = (
                select(models.Task)
                .options(
                    selectinload(models.Task.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.project).selectinload(models.Project.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.creator).selectinload(models.User.creator),
                    selectinload(models.Task.substage).selectinload(models.Stage.parent).selectinload(models.Stage.project).selectinload(models.Project.creator),
                )
                .where(models.Task.substage_uuid == substage_uuid)
            )
            
            async def _op():
                result = await self.session.execute(stmt)
                return result.scalars().all()
            
            tasks_models = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить задачи этапа', exception=common_exceptions.RepositoryError )
            return [self.map_task_to_entity(task) for task in tasks_models]
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить задачи этапа", e)
    
    @classmethod    
    def map_entity_to_task(cls, task_entity: entities.Task) -> models.Task:
        return models.Task(
            uuid=task_entity.uuid,
            name=task_entity.name,
            description=task_entity.description,
            substage_uuid=task_entity.substage.uuid,
            creator_uuid=task_entity.creator.uuid,
            created_at=task_entity.created_at,
            status=cls.map_task_status_to_model(task_entity.status),
            working_days=list(task_entity.working_dates),
            completion_date=task_entity.completion_date
        )
    
    @classmethod
    def map_task_to_entity(cls, task_model: models.Task) -> entities.Task:
        return entities.Task(
            uuid=task_model.uuid,
            name=task_model.name,
            description=task_model.description,
            substage=StageRepository.map_stage_to_entity(task_model.substage),
            creator=UserRepository.map_user_to_entity(task_model.creator),
            created_at=task_model.created_at,
            status=cls.map_task_status_to_domain(task_model.status),
            working_dates=frozenset(task_model.working_days),
            completion_date=task_model.completion_date
            
        )            
    
    @classmethod
    def map_task_status_to_domain(cls, status: models.TaskStatus) -> entities.TaskStatus:
        mapping = {
            models.TaskStatus.PENDING: entities.TaskStatus.PENDING,
            models.TaskStatus.IN_PROGRESS: entities.TaskStatus.IN_PROGRESS,
            models.TaskStatus.COMPLETED: entities.TaskStatus.COMPLETED,
            models.TaskStatus.ARCHIVED: entities.TaskStatus.ARCHIVED,
        }
        return mapping[status]
    
    @classmethod
    def map_task_status_to_model(cls, status: entities.TaskStatus) -> models.TaskStatus:
        mapping = {
            entities.TaskStatus.PENDING: models.TaskStatus.PENDING,
            entities.TaskStatus.IN_PROGRESS: models.TaskStatus.IN_PROGRESS,
            entities.TaskStatus.COMPLETED: models.TaskStatus.COMPLETED,
            entities.TaskStatus.ARCHIVED: models.TaskStatus.ARCHIVED,
        }
        return mapping[status]
    

class PaymentRepository(_RepositoryDebugMixin, common_interfaces.PaymentRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        
    async def create(self, payment: entities.Payment) -> entities.Payment | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        try:
            payment_model = self.map_entity_to_payment(payment)
            
            self.session.add(payment_model)
            
            async def _op():
                return await self.session.flush()
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось создать платеж', exception=common_exceptions.RepositoryError)

            loaded_payment_stmt = (
                select(models.Payment)
                .options(
                    selectinload(models.Payment.subscription)
                    .selectinload(models.Subscription.project)
                    .selectinload(models.Project.creator)
                )
                .where(models.Payment.uuid == payment.uuid)
            )
            loaded_payment_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_payment_stmt,
                error_message="Не удалось создать платеж",
                exception=common_exceptions.RepositoryError,
            )
            loaded_payment = loaded_payment_result.scalar_one_or_none()
            if loaded_payment is None:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать платеж")

            return self.map_payment_to_entity(payment_model=loaded_payment)
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name and "payments_subscription_uuid_fkey" in constraint_name:
                    return common_exceptions.SubscriptionNotFoundError("Подписка не найдена")
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать платеж", e)
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать платеж", e)
        
    async def get_by_uuid(self, payment_uuid: UUID, lock_record: bool = False) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Payment)
                .options(
                    selectinload(models.Payment.subscription)
                    .selectinload(models.Subscription.project)
                    .selectinload(models.Project.creator)
                )
                .where(models.Payment.uuid == payment_uuid)
            )
            
            if lock_record:
                stmt = stmt.with_for_update()
            
            async def _op():
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
            
            payment_model = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить платеж', exception=common_exceptions.RepositoryError )
            if payment_model is None:
                return common_exceptions.PaymentNotFoundError("Платеж не найден")
            return self.map_payment_to_entity(payment_model)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить платеж", e)
    
    async def update(self, payment_uuid: UUID, data: dict[str, Any]) -> entities.Payment | common_exceptions.PaymentNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Payment)
                .options(
                    selectinload(models.Payment.subscription)
                    .selectinload(models.Subscription.project)
                    .selectinload(models.Project.creator)
                )
                .where(models.Payment.uuid == payment_uuid)
            )
            result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                stmt,
                error_message="Не удалось получить платеж",
                exception=common_exceptions.RepositoryError,
            )
            payment = result.scalar_one_or_none()
            if payment is None:
                return common_exceptions.PaymentNotFoundError("Платеж не найден")
            for key, value in data.items():
                setattr(payment, key, value)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось обновить платеж', exception=common_exceptions.RepositoryError )

            loaded_payment_stmt = (
                select(models.Payment)
                .options(
                    selectinload(models.Payment.subscription)
                    .selectinload(models.Subscription.project)
                    .selectinload(models.Project.creator)
                )
                .where(models.Payment.uuid == payment_uuid)
            )
            loaded_payment_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_payment_stmt,
                error_message="Не удалось обновить платеж",
                exception=common_exceptions.RepositoryError,
            )
            loaded_payment = loaded_payment_result.scalar_one_or_none()
            if loaded_payment is None:
                return common_exceptions.PaymentNotFoundError("Платеж не найден")

            return self.map_payment_to_entity(loaded_payment)
        
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить платеж", e)
    
    @classmethod
    def map_currency_to_model(cls, currency: entities.value_objects.CurrencyEnum) -> models.CurrencyEnum:
        mapping = {
            entities.value_objects.CurrencyEnum.RUB: models.CurrencyEnum.RUB,
        }
        return mapping[currency]
    
    @classmethod
    def map_currency_to_domain(cls, currency: models.CurrencyEnum) -> entities.value_objects.CurrencyEnum:
        mapping = {
            models.CurrencyEnum.RUB: entities.value_objects.CurrencyEnum.RUB,
        }
        return mapping[currency]

    @classmethod
    def map_payment_status_to_model(cls, status: entities.PaymentStatus) -> models.PaymentStatus:
        mapping = {
            entities.PaymentStatus.PENDING: models.PaymentStatus.PENDING,
            entities.PaymentStatus.COMPLETED: models.PaymentStatus.COMPLETED,
            entities.PaymentStatus.FAILED: models.PaymentStatus.FAILED,
            entities.PaymentStatus.REFUNDED: models.PaymentStatus.REFUNDED,
        }
        return mapping[status]

    @classmethod
    def map_payment_status_to_domain(cls, status: models.PaymentStatus) -> entities.PaymentStatus:
        mapping = {
            models.PaymentStatus.PENDING: entities.PaymentStatus.PENDING,
            models.PaymentStatus.COMPLETED: entities.PaymentStatus.COMPLETED,
            models.PaymentStatus.FAILED: entities.PaymentStatus.FAILED,
            models.PaymentStatus.REFUNDED: entities.PaymentStatus.REFUNDED,
        }
        return mapping[status]

    @classmethod
    def map_payment_method_to_model(
        cls, method: entities.PaymentMethod | None
    ) -> models.PaymentMethod | None:
        if method is None:
            return None
        mapping = {
            entities.PaymentMethod.CREDIT_CARD: models.PaymentMethod.CREDIT_CARD,
            entities.PaymentMethod.BANK_TRANSFER: models.PaymentMethod.BANK_TRANSFER,
            entities.PaymentMethod.CRYPTOCURRENCY: models.PaymentMethod.CRYPTOCURRENCY,
        }
        return mapping[method]

    @classmethod
    def map_payment_method_to_domain(
        cls, method: models.PaymentMethod | None
    ) -> entities.PaymentMethod | None:
        if method is None:
            return None
        mapping = {
            models.PaymentMethod.CREDIT_CARD: entities.PaymentMethod.CREDIT_CARD,
            models.PaymentMethod.BANK_TRANSFER: entities.PaymentMethod.BANK_TRANSFER,
            models.PaymentMethod.CRYPTOCURRENCY: entities.PaymentMethod.CRYPTOCURRENCY,
        }
        return mapping[method]
    
    @classmethod
    def map_entity_to_payment(cls, payment_entity: entities.Payment) -> models.Payment:
        return models.Payment(
            uuid=payment_entity.uuid,
            subscription_uuid=payment_entity.subscription.uuid,
            amount=payment_entity.amount.amount,
            currency=cls.map_currency_to_model(payment_entity.amount.currency),
            status=cls.map_payment_status_to_model(payment_entity.status),
            payment_method=cls.map_payment_method_to_model(payment_entity.payment_method),
            payment_date=payment_entity.payment_date,
            created_at=payment_entity.created_at,
        )
    
    @classmethod
    def map_payment_to_entity(cls, payment_model: models.Payment) -> entities.Payment:
        return entities.Payment(
            uuid=payment_model.uuid,
            subscription=SubscriptionRepository.map_subscription_to_entity(payment_model.subscription),
            amount=entities.value_objects.MoneyAmount(
                amount=payment_model.amount,
                currency=cls.map_currency_to_domain(payment_model.currency),
            ),
            created_at=payment_model.created_at,
            status=cls.map_payment_status_to_domain(payment_model.status),
            payment_method=cls.map_payment_method_to_domain(payment_model.payment_method),
            payment_date=payment_model.payment_date,
        )

class SubscriptionRepository(_RepositoryDebugMixin, common_interfaces.SubscriptionRepository):
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1
        self._init_debug(config)
        
    async def create(self, subscription: entities.Subscription) -> entities.Subscription | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            subscription_model = self.map_entity_to_subscription(subscription)
            
            self.session.add(subscription_model)
            
            async def _op():
                return await self.session.flush()
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось создать подписку', exception=common_exceptions.RepositoryError)

            loaded_subscription_stmt = (
                select(models.Subscription)
                .options(
                    selectinload(models.Subscription.project).selectinload(models.Project.creator)
                )
                .where(models.Subscription.uuid == subscription.uuid)
            )
            loaded_subscription_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_subscription_stmt,
                error_message="Не удалось создать подписку",
                exception=common_exceptions.RepositoryError,
            )
            loaded_subscription = loaded_subscription_result.scalar_one_or_none()
            if loaded_subscription is None:
                return self._build_error(common_exceptions.RepositoryError, "Не удалось создать подписку")

            return self.map_subscription_to_entity(subscription_model=loaded_subscription)
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, psycopg.errors.ForeignKeyViolation):
                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name and "subscriptions_project_uuid_fkey" in constraint_name:
                    return common_exceptions.ProjectNotFoundError("Проект не найден")
            if isinstance(e.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.SubscriptionAlreadyExistsError("Активная подписка для проекта уже существует")
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать подписку", e)
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось создать подписку", e)
    
    async def get_by_project_uuid(self, project_uuid: UUID) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Subscription)
                .options(
                    selectinload(models.Subscription.project).selectinload(models.Project.creator)
                )
                .where(models.Subscription.project_uuid == project_uuid)
            )
            
            async def _op():
                return await self.session.execute(stmt)
            
            subscription_model = await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось получить подписку по uuid проекта', exception=common_exceptions.RepositoryError )
            subscription = subscription_model.scalar_one_or_none()
            if subscription is None:
                return common_exceptions.SubscriptionNotFoundError("Подписка не найдена")
            return self.map_subscription_to_entity(subscription)
        
        except common_exceptions.RepositoryError as e:
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            return self._build_error(common_exceptions.RepositoryError, "Не удалось получить подписку по uuid проекта", e)
        
    async def update(self, subscription_uuid: UUID, data: dict[str, Any]) -> entities.Subscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.RepositoryError:
        try:
            stmt = (
                select(models.Subscription)
                .options(
                    selectinload(models.Subscription.project).selectinload(models.Project.creator)
                )
                .where(models.Subscription.uuid == subscription_uuid)
            )
            result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                stmt,
                error_message="Не удалось получить подписку",
                exception=common_exceptions.RepositoryError,
            )
            subscription = result.scalar_one_or_none()
            if subscription is None:
                return common_exceptions.SubscriptionNotFoundError("Подписка не найдена")
            for key, value in data.items():
                setattr(subscription, key, value)
            
            async def _op():
                await self.session.flush()
            
            await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message='Не удалось обновить подписку', exception=common_exceptions.RepositoryError )

            loaded_subscription_stmt = (
                select(models.Subscription)
                .options(
                    selectinload(models.Subscription.project).selectinload(models.Project.creator)
                )
                .where(models.Subscription.uuid == subscription_uuid)
            )
            loaded_subscription_result = await _execute_statement_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                loaded_subscription_stmt,
                error_message="Не удалось обновить подписку",
                exception=common_exceptions.RepositoryError,
            )
            loaded_subscription = loaded_subscription_result.scalar_one_or_none()
            if loaded_subscription is None:
                return common_exceptions.SubscriptionNotFoundError("Подписка не найдена")

            return self.map_subscription_to_entity(loaded_subscription)
        
        except common_exceptions.RepositoryError as e:
            await self.session.rollback()
            return self._enrich_error(e)
        
        except (DBAPIError, TimeoutError) as e:
            await self.session.rollback()
            return self._build_error(common_exceptions.RepositoryError, "Не удалось обновить подписку", e)

    @classmethod
    def map_subscription_status_to_domain(cls, status: models.SubscriptionStatus) -> entities.SubscriptionStatus:
        mapping = {
            models.SubscriptionStatus.ACTIVE: entities.SubscriptionStatus.ACTIVE,
            models.SubscriptionStatus.UNACTIVE: entities.SubscriptionStatus.UNACTIVE,
            models.SubscriptionStatus.EXPIRED: entities.SubscriptionStatus.EXPIRED,
            models.SubscriptionStatus.CANCELLED: entities.SubscriptionStatus.CANCELLED,
        }
        return mapping[status]
    
    @classmethod
    def map_subscription_status_to_model(cls, status: entities.SubscriptionStatus) -> models.SubscriptionStatus:
        mapping = {
            entities.SubscriptionStatus.ACTIVE: models.SubscriptionStatus.ACTIVE,
            entities.SubscriptionStatus.UNACTIVE: models.SubscriptionStatus.UNACTIVE,
            entities.SubscriptionStatus.EXPIRED: models.SubscriptionStatus.EXPIRED,
            entities.SubscriptionStatus.CANCELLED: models.SubscriptionStatus.CANCELLED,
        }
        return mapping[status]
    
    @classmethod
    def map_entity_to_subscription(cls, subscription_entity: entities.Subscription) -> models.Subscription:
        return models.Subscription(
            uuid=subscription_entity.uuid,
            project_uuid=subscription_entity.project.uuid,
            created_at=subscription_entity.created_at,
            auto_renew=subscription_entity.auto_renew,
            start_date=subscription_entity.start_date,
            end_date=subscription_entity.end_date,
            status=cls.map_subscription_status_to_model(subscription_entity.status)
        )
    
    @classmethod
    def map_subscription_to_entity(cls, subscription_model: models.Subscription) -> entities.Subscription:
        return entities.Subscription(
            uuid=subscription_model.uuid,
            project=ProjectRepository.map_project_to_entity(subscription_model.project),
            created_at=subscription_model.created_at,
            auto_renew=subscription_model.auto_renew,
            start_date=subscription_model.start_date,
            end_date=subscription_model.end_date,
            status=cls.map_subscription_status_to_domain(subscription_model.status)
        )