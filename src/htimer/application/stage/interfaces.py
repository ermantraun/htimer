from abc import abstractmethod
from typing import Protocol
from domain import entities
from . import exceptions
    
class StageAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_stage(self, actor: entities.User, 
                         project: entities.Project, project_members: list[entities.User], ) -> exceptions.StageAuthorizationError | None:
        pass
    
    @abstractmethod
    def decide_update_stage(self, actor: entities.User, 
                         project: entities.Project, project_members: list[entities.User], ) -> exceptions.StageAuthorizationError | None:
        pass

    @abstractmethod
    def decide_get_stage_list(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.StageAuthorizationError | None:
        pass
