from abc import abstractmethod
from datetime import date
from typing import Protocol


class Clock(Protocol):
    @abstractmethod
    async def now(self) -> date:
        pass
