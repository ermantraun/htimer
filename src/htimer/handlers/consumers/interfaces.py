from abc import abstractmethod
from typing import Protocol

from dishka import AsyncContainer


class BaseConsumer(Protocol):
    @abstractmethod
    def __init__(self, container: AsyncContainer):
        pass

    @abstractmethod
    async def handle(self):
        pass
