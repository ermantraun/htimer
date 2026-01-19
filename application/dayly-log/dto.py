from dataclasses import dataclass
from uuid import UUID
from domain import entities

@dataclass
class CreateDailyLogInDTO:
    date: str
    creator_uuid: UUID
    project_uuid: UUID
    hours_spent: float = 0.0
    description: str = ""
    substage_uuid: UUID | None = None
    
@dataclass
class CreateDailyLogOutDTO:
    daily_log: entities.DailyLog
