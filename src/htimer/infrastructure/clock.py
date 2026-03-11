from htimer.application import common_interfaces
from htimer.application.common_exceptions import InvalidDate
from htimer.config import ClockConfig
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
            return InvalidDate(f'Некорректный формат даты: {date}. Ожидается формат YYYY-MM-DD.')

    def verify_period(self, start_date: common_interfaces.date | None, end_date: common_interfaces.date | None) -> None | InvalidDate:
        if start_date and end_date:
            try:
                start = datetime.strptime(str(start_date), '%Y-%m-%d')
                end = datetime.strptime(str(end_date), '%Y-%m-%d')
                if start > end:
                    return InvalidDate('Дата начала не может быть позже даты окончания.')
            except ValueError:
                return InvalidDate('Некорректный формат даты. Ожидается формат YYYY-MM-DD.')
        elif start_date or end_date:
            return InvalidDate('Дата начала и дата окончания должны быть указаны вместе.')