from datetime import date
from dataclasses import dataclass
from uuid import UUID
from domain import entities
from application.common_interfaces import ActionLink 

@dataclass
class CreateDailyLogInDTO:
    date: str
    creator_uuid: UUID
    project_uuid: UUID
    draft: bool = False
    hours_spent: float = 0.0
    description: str = ""
    substage_uuid: UUID | None = None
    
@dataclass
class CreateDailyLogOutDTO:
    daily_log: entities.DailyLog


@dataclass
class UpdateDailyLogInDTO:
    uuid: UUID
    draft: bool | None = None
    hours_spent: float | None = None
    description: str | None = None
    substage_uuid: UUID | None = None


@dataclass
class UpdateDailyLogOutDTO:
    daily_log: entities.DailyLog


@dataclass
class GetDailyLogInDTO:
    uuid: UUID


@dataclass
class GetDailyLogOutDTO:
    daily_log: entities.DailyLog


@dataclass
class CreateDailyLogFileInDTO:
    daily_log_uuid: UUID
    filename: str


@dataclass
class CreateDailyLogFileOutDTO:
    file: entities.DailyLogFile
    action_link: ActionLink


@dataclass
class GetDailyLogFileInDTO:
    daily_log_uuid: UUID
    file_uuid: UUID


@dataclass
class GetDailyLogFileOutDTO:
    file: entities.DailyLogFile
    action_link: ActionLink


@dataclass
class RemoveDailyLogFileInDTO:
    daily_log_uuid: UUID
    file_uuid: UUID


@dataclass
class GetDailyLogFileListInDTO:
    daily_log_uuid: UUID


@dataclass
class GetDailyLogFileListOutDTO:
    files: list[tuple[entities.DailyLogFile, ActionLink]]


@dataclass
class GetDailyLogListInDTO:
    project_uuid: UUID
    start_date: date
    end_date: date
    user_uuid: UUID | None = None


@dataclass
class GetDailyLogListOutDTO:
    daily_logs: list[entities.DailyLog]



