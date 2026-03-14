from htimer.application import common_interfaces
from htimer.config import Config

from . import interfaces


class Logger(common_interfaces.Logger):
    def __init__(self, config: Config, clock: interfaces.Clock) -> None:
        self.config = config.logger_config
        self.clock = clock

    async def info(self, operation: str, message: str) -> None:
        print(f"[INFO] {operation}: {message}, Time: {await self.clock.now()}")
