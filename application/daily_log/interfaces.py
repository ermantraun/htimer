from typing import Protocol
from abc import abstractmethod
from domain import entities
from . import exceptions

class DailyLogAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_daily_log(self, actor: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.DayliLogAuthorizationError | None:
        pass

    @abstractmethod
    def decide_update_daily_log(self, actor: entities.User,  daily_log: entities.DailyLog) -> exceptions.DayliLogAuthorizationError | None:
        pass
    
    @abstractmethod
    def decide_get_daily_log(self, actor: entities.User, daily_log: entities.DailyLog, project_members: list[entities.User]) -> exceptions.DayliLogAuthorizationError | None:
        pass

    @abstractmethod
    def decide_get_daily_log_list(self, actor: entities.User, target: entities.User, project: entities.Project, project_members: list[entities.User]) -> exceptions.DayliLogAuthorizationError | None:
        pass

    


