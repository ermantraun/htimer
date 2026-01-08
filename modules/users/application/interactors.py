from uuid import uuid4
from modules.users.domain import entities
from application.common_interfaces import DBSession
from . import interfaces
from . import validators
from . import dto
from . import exceptions


#Вытащить исключения наверх

class CreateUserInteractor:
    def __init__(self, session: DBSession, context: interfaces.UserContext, user_getter: interfaces.UserGetter,  hash_generator: interfaces.HashGenerator, user_creator: interfaces.UserCreator, validator: validators.CreateUserValidator):
        self.user_getter = user_getter
        self.user_creator = user_creator
        self.validator = validator
        self.context = context
        self.hash_generator = hash_generator
        self.session = session
    async def execute(self, data: dto.CreateUserInDTO) -> dto.CreateUserOutDTO:

        current_user_uuid = self.context.get_current_user_uuid()

        if isinstance(current_user_uuid, exceptions.InvalidToken):
            raise current_user_uuid


        user = await self.user_getter.get(current_user_uuid)
        
        

        if isinstance(user, exceptions.UserRepositoryError):
            raise user

 
        error = self.validator.validate(user, data)
        if error is not None:
            raise error

        password_hash = self.hash_generator.generate(data.password)
        
        user = entities.User(
            uuid=uuid4(),
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            creator_uuid=user.uuid,
            is_active=data.is_active if data.is_active is not None else True,
            is_archived=data.is_archived if data.is_archived is not None else False,
            is_admin=data.is_admin
        )
        user = await self.user_creator.create(user)

        if isinstance(user, exceptions.UserRepositoryError):
            raise user

        await self.session.commit()
        
        return dto.CreateUserOutDTO(
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_archived=user.is_archived,
            is_admin=user.is_admin
        )
    
    
class UpdateUserInteractor:
    def __init__(self, session: DBSession, user_updater: interfaces.UserUpdater, user_projects_getter: interfaces.UserProjectsGetter, user_getter: interfaces.UserGetter, context: interfaces.UserContext, validator: validators.UpdateUserValidator):
        self.user_context = context
        self.validator = validator
        self.user_updater = user_updater
        self.user_getter = user_getter
        self.user_projects_getter = user_projects_getter
        self.session = session
        
    async def execute(self,  data: dto.UpdateUserInDTO) -> dto.UpdateUserOutDTO:
        error = None
        if data.uuid is not None:
            
            user_uuid = self.user_context.get_current_user_uuid()
            
            if isinstance(user_uuid, exceptions.InvalidToken):
                raise user_uuid

            admin = await self.user_getter.get(user_uuid)
            user = await self.user_getter.get(data.uuid)
            
            if isinstance(user, exceptions.UserRepositoryError):
                raise user
            
            if isinstance(admin, exceptions.UserRepositoryError):
                raise admin
            
            
            admin_projects = await self.user_projects_getter.get(admin.uuid)
            user_projects = await self.user_projects_getter.get(user.uuid)
            
            if isinstance(admin_projects, exceptions.UserRepositoryError):
                raise admin_projects
            
            
            
            if isinstance(user_projects, exceptions.UserRepositoryError):
                raise user_projects

            error = self.validator.validate(user, data, admin=admin, user_projects=user_projects, admin_projects=admin_projects)
            
        else:
            current_user_uuid = self.user_context.get_current_user_uuid()
            
            if isinstance(current_user_uuid, exceptions.InvalidToken):
                raise current_user_uuid
            
            user = await self.user_getter.get(current_user_uuid)
            
            if isinstance(user, exceptions.UserRepositoryError):
                raise user
            
            error = self.validator.validate(user, data)
            
        if error is not None:
            raise error
    

        user = await self.user_updater.update(data)
        if isinstance(user, exceptions.UserRepositoryError):
            raise user
        
        await self.session.commit()
        
        return dto.UpdateUserOutDTO(
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_archived=user.is_archived,
            is_admin=user.is_admin
        )




class GetUsersInteractor:
    def __init__(self, user_getter: interfaces.UserGetter, context: interfaces.UserContext, user_projects_getter: interfaces.UserProjectsGetter, projects_users_getter: interfaces.ProjectsUsersGetter, get_users_list_validator: validators.GetUsersListValidator):
        self.user_getter = user_getter
        self.user_context = context
        self.user_projects_getter = user_projects_getter
        self.projects_users_getter = projects_users_getter
        self.get_users_list_validator = get_users_list_validator
    async def execute(self, data: dto.GetUsersInDto) -> list[dto.UpdateUserOutDTO]:

        current_user_uuid = self.user_context.get_current_user_uuid()
        
        if isinstance(current_user_uuid, exceptions.InvalidToken):
            raise current_user_uuid
        
        user = await self.user_getter.get(current_user_uuid)
        
        if isinstance(user, exceptions.UserRepositoryError):
            raise user
        
        
        user_projects = await self.user_projects_getter.get(current_user_uuid)
        
        if isinstance(user_projects, exceptions.UserRepositoryError):
            raise user_projects
        
        error = self.get_users_list_validator.validate(data, user,  {p.name for p in user_projects})
        
        if error is not None:
            raise error
        
        
        projects_uuid = [project.uuid for project in user_projects if project.name in data.projects_names] if data.projects_names else None
        
        users = await self.projects_users_getter.get(
            projects_uuid=projects_uuid,
            is_active=data.status
        )
        
        if isinstance(users, exceptions.UserRepositoryError):
            raise users
        
        return [
            dto.UpdateUserOutDTO(
                name=user.name,
                email=user.email,
                is_active=user.is_active,
                is_archived=user.is_archived,
                is_admin=user.is_admin
            ) for user in users
        ]


