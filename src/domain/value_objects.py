from dataclasses import dataclass
from datetime import date
import enum

@dataclass(frozen=True)
class WorkingDates:
    dates: tuple[date, ...]
    
    def __post_init__(self):

        if len(set(self.dates)) != len(self.dates):
            raise ValueError("Duplicate dates are not allowed")
        

class CurrencyEnum(str, enum.Enum):
    RUB = "RUB"


@dataclass
class MoneyAmount:
    amount: float
    currency: CurrencyEnum = CurrencyEnum.RUB
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    
