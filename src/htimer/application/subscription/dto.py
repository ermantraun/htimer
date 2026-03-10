
from dataclasses import dataclass
from uuid import UUID
from domain import entities

@dataclass
class CreateSubscriptionInDTO:
    project_uuid: UUID
    
@dataclass
class CreateSubscriptionOutDTO:
    subscription: entities.Subscription
    
@dataclass
class CreatePaymentInDTO:
    uuid: UUID
    project_uuid: UUID
    amount: float
    currency: str = "RUB"
    
@dataclass
class CreatePaymentOutDTO:
    process_payment_link: str
    
@dataclass
class CompletePaymentInDTO:
    payment_uuid: UUID



@dataclass
class UpdateSubscriptionInDTO:
    project_uuid: UUID
    auto_renew: bool | None = None
    status: str | None = None

@dataclass
class ExtendSubscriptionInDTO:
    project_uuid: UUID
    payment_uuid: UUID
    
@dataclass 
class ActivateSubscriptionInDTO:
    project_uuid: UUID
    payment_uuid: UUID
    
@dataclass
class CompletePaymentAndUpdateSubscriptionInDTO:
    project_uuid: UUID
    payment_uuid: UUID

@dataclass
class CompletePaymentAndUpdateSubscriptionOutDTO:
    subscription: entities.Subscription
    


