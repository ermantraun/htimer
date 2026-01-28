from dataclasses import dataclass
from datetime import date
import enum

@dataclass(frozen=True)
class WorkingDates:
    dates: tuple[date, ...]
    complete_date: date | None 
    
    def __post_init__(self):

        if len(set(self.dates)) != len(self.dates):
            raise ValueError("Duplicate dates are not allowed")

        if self.complete_date not in self.dates:
            raise ValueError("Complete date must be one of the working dates")

class CurrencyEnum(str, enum.Enum):
    RUB = "RUB"


@dataclass
class MoneyAmount:
    amount: float
    currency: CurrencyEnum = CurrencyEnum.RUB
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    
