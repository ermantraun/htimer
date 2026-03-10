from abc import abstractmethod
from typing import Protocol
from datetime import date


class Clock(Protocol):
    @abstractmethod
    async def now(self) -> date:
        pass