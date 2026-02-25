from typing import Protocol
from abc import abstractmethod
from dishka import AsyncContainer



class BaseConsumer(Protocol):

    @abstractmethod
    def __init__(self, container: AsyncContainer):
        pass

    @abstractmethod
    async def handle(self):
        pass