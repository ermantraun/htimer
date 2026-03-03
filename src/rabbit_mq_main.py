import asyncio
from concurrent.futures import ProcessPoolExecutor
from collections.abc import Sequence
import signal
import os
from typing import Any
import dishka
from handlers.consumers import consumers
from handlers.consumers.interfaces import BaseConsumer
from ioc.app import AppProvider
from utils import MessageBrokerInitializer
from config import Config


async def run_consumer(consumer_cls: type[BaseConsumer]) -> None:
    container = dishka.make_async_container(
        AppProvider(),
        context={Config: Config()},
    )

    consumer = consumer_cls(container)

    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=2) as executor:
        tasks = [loop.run_in_executor(executor, consumer.handle) for _ in range(2)]
        
        done, _ =  await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        if done:
            for task in done:
                if task.exception():
                    print(f"Consumer {consumer_cls.__name__} raised an exception: {task.exception()}")
                    on_shutdown_signal()
                    break


async def run_consumers(consumers: Sequence[type[BaseConsumer]]) -> None:
    await asyncio.gather(*(run_consumer(c) for c in consumers))


def on_shutdown_signal(*_: Any) -> None:
    os.killpg(os.getpgrp(), signal.SIGTERM)


def main() -> None:
    os.setpgrp()

    signal.signal(signal.SIGTERM, on_shutdown_signal)
    signal.signal(signal.SIGINT, on_shutdown_signal)

    MessageBrokerInitializer(Config()).init()
    asyncio.run(run_consumers(consumers))


if __name__ == "__main__":
   main()