from abc import abstractmethod
from typing import Protocol
from domain import entities
import exceptions
    

class StageCreateAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_stage(self, actor: entities.User, 
                         project: entities.Project, project_members: list[entities.User], ) -> exceptions.StageAuthorizationError | None:
        pass

class StageUpdateAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_update_stage(self, actor: entities.User, 
                         project: entities.Project, project_members: list[entities.User], ) -> exceptions.StageAuthorizationError | None:
        pass