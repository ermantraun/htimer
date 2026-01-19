from typing import Protocol
from abc import abstractmethod
from domain import entities
import exceptions

class DailyLogCreateAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_daily_log(self, project_members: list[entities.User]) -> exceptions.DayliLogAuthorizationError | None:
        pass
    
