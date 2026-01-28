from abc import abstractmethod
from typing import Protocol
from uuid import UUID
from domain import entities
from . import exceptions

class UserAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_update_user(
        self,
        
        actor: entities.User,
        target: entities.User,

    ) -> exceptions.UserAuthorizationError | None:
        pass
    
    @abstractmethod
    def decide_create_user(self, actor: entities.User) -> exceptions.UserAuthorizationError | None:
        pass 
    
    @abstractmethod
    def decide_get_users_list(
        self,
        actor: entities.User,
        projects_names: set[str],
        actor_projects_names: set[str],
    ) -> exceptions.UserAuthorizationError | None:
        pass
    
    @abstractmethod
    def decide_reset_password(self, actor: entities.User, target: entities.User) -> exceptions.UserAuthorizationError | None:
        pass


class HashVerifier(Protocol):
    
    @abstractmethod
    def verify(self, plain_password: str, hashed_text: str) -> bool:
        pass

class HashGenerator(Protocol):
    @abstractmethod
    def generate(self, plain_password: str) -> str:
        pass

class TokenGenerator(Protocol):

    @abstractmethod
    def generate(self, user_uuid: UUID) -> str:
        pass





