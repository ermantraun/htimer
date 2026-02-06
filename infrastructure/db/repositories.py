from typing import Any, Awaitable, Callable
from uuid import UUID
import asyncio

from sqlalchemy import select, insert, and_
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import psycopg.errors

from application import common_exceptions, common_interfaces
from domain import entities
from . import models

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
                await session.rollback()
                if attempt >= idempotent_retries:
                    raise exception(error_message) from exc

                attempt += 1
                await asyncio.sleep(base_backoff * (attempt + 1))

class UserRepository(common_interfaces.UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
        self._idempotent_retries = 2
        self._base_backoff = 0.1

    async def create(self, data: entities.User) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserRepositoryError:
        try:

            new_user = models.User(
                uuid=data.uuid,
                name=data.name,
                email=data.email,
                password_hash=data.password_hash,
                creator_uuid=data.creator.uuid if getattr(data, "creator", None) else None,
                role=self._map_role_to_model(data.role),
                status=self._map_status_to_model(data.status),
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

            return self._map_user_to_entity(new_user)
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.EmailAlreadyExistsError(
                "Пользователь с таким email уже существует"
            )
        except common_exceptions.UserRepositoryError as exc:
            await self.session.rollback()
            return exc
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.UserRepositoryError("Не удалось создать пользователя")

    async def update(self, user_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.User | common_exceptions.EmailAlreadyExistsError | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        try:
            user_model = await self._get_user_model(user_uuid, lock_record=not release_record)
            
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

            if release_record:
                await self.session.refresh(user_model)

            return self._map_user_to_entity(user_model)
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.EmailAlreadyExistsError(
                "Пользователь с таким email уже существует"
            )
        except common_exceptions.UserRepositoryError as exc:
            await self.session.rollback()
            return exc
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.UserRepositoryError("Не удалось обновить пользователя")

    async def get_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        try:
            async def _op():
                return await self._fetch_user_by_email(email)
            
            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff,
                _op,
                error_message="Не удалось получить пользователя по email",
                exception=common_exceptions.UserRepositoryError
            )
        except common_exceptions.UserRepositoryError as exc:
            return exc

    async def get_by_uuid(self, user_uuid: UUID, lock_record: bool = False) -> entities.User | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        try:
            def _op():
                return self._fetch_user_by_uuid(user_uuid, lock_record=lock_record)
            
            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff,
                _op,
                error_message="Не удалось получить пользователя по uuid",
                exception=common_exceptions.UserRepositoryError
            )
        except common_exceptions.UserRepositoryError as exc:
            return exc

    async def get_list(self, users_uuid: list[UUID]) -> list[entities.User] | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        try:
            async def _op() -> list[entities.User] | common_exceptions.UserNotFoundError:
                stmt = (
                    select(models.User)
                    .options(selectinload(models.User.creator))
                    .where(models.User.uuid.in_(users_uuid))
                )
                
                result = await self.session.execute(stmt)
                users = result.scalars().all()

                if len(users) != len(users_uuid):
                    return common_exceptions.UserNotFoundError("Один или несколько пользователей не найдены")

                return [self._map_user_to_entity(user) for user in users]

            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить список пользователей", exception=common_exceptions.UserRepositoryError)
        except common_exceptions.UserRepositoryError as exc:
            return exc

    async def get_projects(self, user_uuid: UUID | None) -> list[entities.Project] | common_exceptions.UserNotFoundError | common_exceptions.UserRepositoryError:
        try:
            async def _op() -> list[entities.Project] | common_exceptions.UserNotFoundError:
                if user_uuid is None:
                    return []

                user_model = await self._get_user_model(user_uuid)
                if user_model is None:
                    return common_exceptions.UserNotFoundError("Пользователь не найден")

                owned_stmt = select(models.Project).options(selectinload(models.Project.creator)).where(
                    models.Project.creator_uuid == user_uuid
                )
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

                return [self._map_project_to_entity(project) for project in projects_models.values()]

            return await _execute_idempotent(self.session, self._idempotent_retries, self._base_backoff, _op, error_message="Не удалось получить проекты пользователя", exception=common_exceptions.UserRepositoryError)
        except common_exceptions.UserRepositoryError as exc:
            return exc
    
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
            user_model.role = self._map_role_to_model(data["role"])
        if "status" in data:
            user_model.status = self._map_status_to_model(data["status"])
        if "last_login" in data:
            user_model.last_login = data["last_login"]

    async def _fetch_user_by_email(self, email: str) -> entities.User | common_exceptions.UserNotFoundError:
        stmt = (
            select(models.User)
            .options(selectinload(models.User.creator))
            .where(models.User.email == email)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return common_exceptions.UserNotFoundError("Пользователь не найден")
        return self._map_user_to_entity(user)

    async def _fetch_user_by_uuid(
        self, user_uuid: UUID, *, lock_record: bool = False
    ) -> entities.User | common_exceptions.UserNotFoundError:
        user_model = await self._get_user_model(user_uuid, lock_record=lock_record)
        if user_model is None:
            return common_exceptions.UserNotFoundError("Пользователь не найден")
        return self._map_user_to_entity(user_model)

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

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    def _map_user_to_entity(cls, user_model: models.User) -> entities.User:
        creator_entity = (
            cls._map_user_to_entity(user_model.creator)
            if user_model.creator is not None
            else None
        )

        return entities.User(
            uuid=user_model.uuid,
            name=user_model.name,
            email=user_model.email,
            password_hash=user_model.password_hash,
            creator=creator_entity,  # type: ignore[arg-type]
            role=cls._map_role_to_domain(user_model.role),
            status=cls._map_status_to_domain(user_model.status),
            created_at=user_model.created_at,
            last_login=user_model.last_login,
        )

    @classmethod
    def _map_project_to_entity(cls, project_model: models.Project) -> entities.Project:
        return entities.Project(
            uuid=project_model.uuid,
            name=project_model.name,
            description=project_model.description,
            creator=cls._map_user_to_entity(project_model.creator),
            created_at=project_model.created_at,
            status=cls._map_project_status_to_domain(project_model.status),
            start_date=project_model.start_date,
            end_date=project_model.end_date,
        )

    @classmethod
    def _map_role_to_domain(cls, role: models.UserRole) -> entities.UserRole:
        return entities.UserRole.ADMIN if role is models.UserRole.ADMIN else entities.UserRole.EXECUTOR

    @classmethod
    def _map_role_to_model(cls, role: entities.UserRole) -> models.UserRole:
        return models.UserRole.ADMIN if role is entities.UserRole.ADMIN else models.UserRole.USER

    @classmethod
    def _map_status_to_domain(cls, status: models.UserStatus) -> entities.UserStatus:
        mapping = {
            models.UserStatus.ACTIVE: entities.UserStatus.ACTIVE,
            models.UserStatus.BLOCKED: entities.UserStatus.BLOCKED,
            models.UserStatus.ARCHIVED: entities.UserStatus.ARCHIVED,
        }
        return mapping[status]

    @classmethod
    def _map_status_to_model(cls, status: entities.UserStatus) -> models.UserStatus:
        mapping = {
            entities.UserStatus.ACTIVE: models.UserStatus.ACTIVE,
            entities.UserStatus.BLOCKED: models.UserStatus.BLOCKED,
            entities.UserStatus.ARCHIVED: models.UserStatus.ARCHIVED,
        }
        return mapping[status]

    @classmethod
    def _map_project_status_to_domain(cls, status: models.ProjectStatus) -> entities.ProjectStatus:
        mapping = {
            models.ProjectStatus.ACTIVE: entities.ProjectStatus.ACTIVE,
            models.ProjectStatus.ARCHIVED: entities.ProjectStatus.ARCHIVED,
            models.ProjectStatus.BLOCKED: entities.ProjectStatus.BLOCKED,
            models.ProjectStatus.COMPLETED: entities.ProjectStatus.COMPLETED,
        }
        return mapping[status]



class ProjectRepository(common_interfaces.ProjectRepository):
    def __init__(self, session: AsyncSession, idempotent_retries: int = 2, base_backoff: float = 0.1):
        self.session = session
        self._idempotent_retries = idempotent_retries
        self._base_backoff = base_backoff
        
    async def create(self, data: entities.Project) -> entities.Project | common_exceptions.UserAlreadyHasProjectError | common_exceptions.UserNotFoundError | common_exceptions.ProjectRepositoryError:
        try: 
            project = models.Project(
                uuid=data.uuid,
                name=data.name,
                description=data.description,
                creator_uuid=data.creator.uuid,
                start_date=data.start_date,
                end_date=data.end_date,
                status=self._map_project_status_to_model(data.status),
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
            
            return self._map_project_to_entity(project)
        
        except IntegrityError as exc:
            await self.session.rollback()
            if isinstance(exc.orig, psycopg.errors.ForeignKeyViolation):
                return common_exceptions.UserNotFoundError("Пользователь не найден")
            elif isinstance(exc.orig, psycopg.errors.UniqueViolation):
                return common_exceptions.UserAlreadyHasProjectError("Проект с таким именем уже существует")
            else:
                return common_exceptions.ProjectRepositoryError("Не удалось создать проект")
        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return exc
        
        
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.ProjectRepositoryError("Не удалось создать проект")
        
    async def update(self, project_uuid: UUID, data: dict[str, Any], release_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.UserAlreadyHasProjectError | common_exceptions.ProjectRepositoryError:
        try:
            project_model = await self._get_project_model(project_uuid, lock_record=not release_record)
            
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

            if release_record:
                await self.session.refresh(project_model)
        
            return self._map_project_to_entity(project_model)
        
        except IntegrityError:
            await self.session.rollback()
            return common_exceptions.UserAlreadyHasProjectError("Проект с таким именем уже существует")

        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return exc

        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.ProjectRepositoryError("Не удалось обновить проект")
    
    async def get_by_uuid(self, project_uuid: UUID, lock_record: bool = False) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.ProjectRepositoryError:
        
        try: 
            project = await self._get_project_model(project_uuid, lock_record)
            
            if project is None: 
                return common_exceptions.ProjectNotFoundError("Проект не найден")
            
            return self._map_project_to_entity(project)

        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return exc
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.ProjectRepositoryError("Не удалось получить проект")
            
        
    async def get_by_name(self, user_uuid: UUID, project_name: str) -> entities.Project | common_exceptions.ProjectNotFoundError | common_exceptions.ProjectRepositoryError:
        try:
            stmt = (
                select(models.Project)
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

            return self._map_project_to_entity(project_model) 
        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return exc
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.ProjectRepositoryError("Не удалось получить проект")
    
    async def add_members(self, members: list[entities.MemberShip]) -> list[entities.MemberShip] | common_exceptions.ProjectNotFoundError | common_exceptions.UserNotFoundError | common_exceptions.UserAlreadyProjectMemberError | common_exceptions.ProjectRepositoryError:
        try: 
            
            members_models: list[models.MemberShip] = [models.MemberShip(
                uuid=membership.uuid,
                project_uuid=membership.project.uuid,
                user_uuid=membership.user.uuid,
                assigned_by_uuid=membership.assigned_by.uuid,
                joined_at=membership.joined_at
            ) for membership in members]

            insert_members_smtp = insert(models.MemberShip).values(members)
            
            async def _op() -> None:
                await self.session.execute(insert_members_smtp)
            
            await _execute_idempotent(
                self.session,
                self._idempotent_retries,
                self._base_backoff,
                _op,
                error_message="Не удалось добавить пользователей",
                exception=common_exceptions.ProjectRepositoryError,
            )
        

            return self.map_members_models_to_entities(members_models)
        
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
            return common_exceptions.ProjectRepositoryError("Не удалось добавить пользователей")
        except common_exceptions.ProjectRepositoryError as exc:
            await self.session.rollback()
            return exc
        except (OperationalError, DBAPIError) as exc:
            await self.session.rollback()
            return common_exceptions.ProjectRepositoryError("Не удалось добавить пользователей")
        
        
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
                project=entities.Project(uuid=membership.project_uuid, name="", description="", creator=None, created_at=None, status=entities.ProjectStatus.ACTIVE, start_date=None, end_date=None),  # type: ignore[arg-type]
                user=entities.User(uuid=membership.user_uuid, name="", email="", password_hash="", creator=None, role=entities.UserRole.EXECUTOR, status=entities.UserStatus.ACTIVE, created_at=None, last_login=None),  # type: ignore[arg-type]
                assigned_by=entities.User(uuid=membership.assigned_by_uuid, name="", email="", password_hash="", creator=None, role=entities.UserRole.EXECUTOR, status=entities.UserStatus.ACTIVE, created_at=None, last_login=None),  # type: ignore[arg-type]
                joined_at=membership.joined_at
            ) for membership in memberships
        ]
    
    @classmethod
    def _map_project_entitie_to_model(cls, entitie: entities.Project) -> models.Project:
        return models.Project(
            uuid=entitie.uuid,
            name=entitie.name,
            description=entitie.description,
            creator_uuid=entitie.creator.uuid,
            start_date=entitie.start_date,
            end_date=entitie.end_date,
            status=cls._map_project_status_to_model(entitie.status),
            created_at=entitie.created_at,
        )

    @classmethod
    def _map_project_model_to_entity(cls, model: models.Project) -> entities.Project:
        return entities.Project(
            uuid=model.uuid,
            name=model.name,
            description=model.description,
            creator=UserRepository._map_user_to_entity(model.creator),  # type: ignore[reportPrivateUsage]
            created_at=model.created_at,
            status=cls._map_project_status_to_domain(model.status),
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
            project_model.status = self._map_project_status_to_model(data["status"])
        if "start_date" in data:
            project_model.start_date = data["start_date"]
        if "end_date" in data:
            project_model.end_date = data["end_date"]
    
    @classmethod
    def _map_project_status_to_model(cls, status: entities.ProjectStatus) -> models.ProjectStatus:
        mapping = {
            entities.ProjectStatus.ACTIVE: models.ProjectStatus.ACTIVE,
            entities.ProjectStatus.ARCHIVED: models.ProjectStatus.ARCHIVED,
            entities.ProjectStatus.BLOCKED: models.ProjectStatus.BLOCKED,
            entities.ProjectStatus.COMPLETED: models.ProjectStatus.COMPLETED,
        }
        return mapping[status]

    @classmethod
    def _map_project_status_to_domain(cls, status: models.ProjectStatus) -> entities.ProjectStatus:
        mapping = {
            models.ProjectStatus.ACTIVE: entities.ProjectStatus.ACTIVE,
            models.ProjectStatus.ARCHIVED: entities.ProjectStatus.ARCHIVED,
            models.ProjectStatus.BLOCKED: entities.ProjectStatus.BLOCKED,
            models.ProjectStatus.COMPLETED: entities.ProjectStatus.COMPLETED,
        }
        return mapping[status]

    @classmethod
    def _map_project_to_entity(cls, project_model: models.Project) -> entities.Project:
        creator = entities.User(
            uuid=project_model.creator.uuid,
            name=project_model.creator.name,
            email=project_model.creator.email,
            password_hash=project_model.creator.password_hash,
            creator=None,  # type: ignore[arg-type]
            role=UserRepository._map_role_to_domain(project_model.creator.role),  # type: ignore[reportPrivateUsage]
            status=UserRepository._map_status_to_domain(project_model.creator.status),  # type: ignore[reportPrivateUsage]
            created_at=project_model.creator.created_at,
            last_login=project_model.creator.last_login,
        )
        return entities.Project(
            uuid=project_model.uuid,
            name=project_model.name,
            description=project_model.description,
            creator=creator,  # type: ignore[arg-type]
            created_at=project_model.created_at,
            status=cls._map_project_status_to_domain(project_model.status),
            start_date=project_model.start_date,
            end_date=project_model.end_date,
        )

