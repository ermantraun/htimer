from dataclasses import dataclass
from datetime import date
from uuid import UUID
from htimer.domain import entities

@dataclass
class CreateReportRequestInDTO:
    project_id: UUID
    start_date: date | None = None
    end_date: date | None = None
    target_users: list[UUID] | None = None

@dataclass
class CreateReportRequestOutDTO:
    report: entities.Report

@dataclass
class CreateReportInDTO:
    report_id: str

