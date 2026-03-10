from abc import abstractmethod
from typing import Protocol
from datetime import date


class Clock(Protocol):
    @abstractmethod
    def now(self) -> date:
        pass