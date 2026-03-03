import aio_pika
from dishka import AsyncContainer
import signal
from typing import Any
from uuid import UUID
from config import Config
from application.reports import interactors, dto
from application import common_interfaces
from domain import entities

from .interfaces import BaseConsumer


shutdown_signal_received = False

def on_shutdown_signal(*_: Any) -> None:
    global shutdown_signal_received
    shutdown_signal_received = True

signal.signal(signal.SIGINT, on_shutdown_signal)
signal.signal(signal.SIGTERM, on_shutdown_signal)

async def try_retry(exchange: aio_pika.abc.AbstractExchange, message: aio_pika.abc.AbstractIncomingMessage, config: Config):

    headers = message.headers or {}
    raw_retry = headers.get("x-retry-count", 0)

    if isinstance(raw_retry, (bytes, bytearray)):
        try:
            raw_retry = raw_retry.decode("utf-8")
        except Exception:
            raw_retry = 0

    if isinstance(raw_retry, str):
        retry_count = int(raw_retry) if raw_retry.isdigit() else 0
    elif isinstance(raw_retry, int):
        retry_count = raw_retry
    else:
        retry_count = 0

    if retry_count < config.rabbitmq.retry_count:
        await exchange.publish(
            aio_pika.Message(body=message.body, 
                             delivery_mode=aio_pika.DeliveryMode.PERSISTENT, 
                             message_id=message.message_id, headers={"x-retry-count": retry_count + 1}),
            routing_key=config.rabbitmq.report_queue_name
        )
        return True
    
    return False

class CreateReportConsumer(BaseConsumer):

    def __init__(self, container: AsyncContainer):
        self.container = container

    async def handle(self):

        async with self.container() as request_scope:
            report_repository = await request_scope.get(common_interfaces.ReportRepository)
            report_interactor = await request_scope.get(interactors.CreateReportInteractor)
            logger = await request_scope.get(common_interfaces.Logger)
            config = await request_scope.get(Config)
            channel = await request_scope.get(aio_pika.abc.AbstractChannel)
            
            queue = await channel.get_queue(config.rabbitmq.report_queue_name, ensure=True)
            exchange = await channel.get_exchange(config.rabbitmq.exchange_name + "_dlx", ensure=True)
            exchange_dlx = await channel.get_exchange(config.rabbitmq.exchange_name + "_dlx", ensure=True)
            
            async with queue.iterator() as queue_iter:
                if not shutdown_signal_received:
                    async for message in queue_iter:
                        msg_id = message.message_id

                        if msg_id is None:
                            
                            if not await try_retry(exchange, message, config):
                                await exchange_dlx.publish(
                                    aio_pika.Message(body=message.body, 
                                                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                                    message_id="unknown_id"),
                                    routing_key=config.rabbitmq.report_queue_name + "_dlx"
                                )
                                await logger.info(operation="report_generation_failed", message=f'msg_id: unknown_id, error: Missing message_id')

                            continue

                        try:

                            report = await report_repository.get_by_uuid(report_uuid=UUID(msg_id))

                            if isinstance(report, Exception):
                                raise report
                            
                            if report.status != entities.ReportStatus.PENDING:
                                await message.ack()
                                continue

                            await report_interactor.execute(dto.CreateReportInDTO(report_id=msg_id))

                            await message.ack()
                            await logger.info(operation="report_generation_success", message=msg_id)

                        except Exception as e:
                            if not await try_retry(exchange, message, config):
                                
                                await exchange_dlx.publish(
                                    aio_pika.Message(body=message.body, 
                                                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                                    message_id=msg_id),
                                    routing_key=config.rabbitmq.report_queue_name + "_dlx"
                                )

                                exc = await report_repository.update(report_uuid=UUID(msg_id), data={"status": entities.ReportStatus.FAILED})

                                if isinstance(exc, Exception):
                                    await logger.info(operation="report_status_update_failed", message=f'msg_id: {msg_id}, error: {str(e)}, details: Cant update report status to FAILED after exhausting retries')


                                await logger.info(operation="report_generation_failed", message=f'msg_id: {msg_id}, error: {str(e)}')
                else:
                    raise StopAsyncIteration
                        
                    







