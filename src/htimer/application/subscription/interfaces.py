from typing import Protocol
from abc import abstractmethod
from htimer.domain import entities
from . import exceptions

class SubscriptionAuthorizationPolicy(Protocol):
    @abstractmethod
    def decide_create_subscription(self, actor: entities.User, project: entities.Project) -> exceptions.SubscriptionAuthorizationError | None:
        pass
    
    @abstractmethod
    def decide_create_payment(self, actor: entities.User, project: entities.Project) -> exceptions.SubscriptionAuthorizationError | None:
        pass

    @abstractmethod
    def decide_update_subscription(self, actor: entities.User, project: entities.Project) -> exceptions.SubscriptionAuthorizationError | None:
        pass
