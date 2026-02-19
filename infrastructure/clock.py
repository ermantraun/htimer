from application import common_interfaces
from application.common_exceptions import InvalidDate
from config import ClockConfig
from datetime import datetime
import pytz


class SystemClock(common_interfaces.Clock):
    def __init__(self, config: ClockConfig):
        self.timezone = pytz.timezone(config.timezone)

    async def now(self) -> datetime:
        return datetime.now(self.timezone)

    async def now_date(self) -> datetime:
        return datetime.now(self.timezone)

    def verify_date(self, date: str) -> str | InvalidDate:
        try:
            datetime.strptime(date, '%Y-%m-%d')
            return date
        except ValueError:
            return InvalidDate(f'Invalid date format: {date}. Expected format: YYYY-MM-DD')

