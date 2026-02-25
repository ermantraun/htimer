import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Sequence
import dishka
from handlers.consumers import consumers
from handlers.consumers.interfaces import BaseConsumer
from ioc.app import AppProvider
from utils import MessageBrokerInitializer
from config import Config

#Добавить обработку ошибок и корректную остановку потребителей при завершении приложения.

async def run_consumer(consumer_cls: type[BaseConsumer]) -> None:
    container = dishka.make_async_container(
        AppProvider(),
        context={Config: Config()},
    )

    consumer = consumer_cls(container)

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=2) as executor:
        tasks = [loop.run_in_executor(executor, consumer.handle) for _ in range(10)]
        await asyncio.gather(*tasks)


async def run_consumers(consumers: Sequence[type[BaseConsumer]]) -> None:
    await asyncio.gather(*(run_consumer(c) for c in consumers))


if __name__ == "__main__":
    MessageBrokerInitializer(Config()).init()
    asyncio.run(run_consumers(consumers))