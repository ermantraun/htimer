from config import Config
from application.reports import interactors
from application import common_interfaces
from domain import entities
from uuid import UUID

import aio_pika


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


class ReportConsumer:

    def __init__(self, config: Config, report_repository: common_interfaces.ReportRepository, report_interactor: interactors.CreateReportInteractor, channel: aio_pika.abc.AbstractChannel, logger: common_interfaces.Logger):
        self.config = config
        self.report_repository = report_repository  
        self.report_interactor = report_interactor
        self.channel = channel
        self.logger = logger

    async def handle_create(self):
        queue = await self.channel.get_queue(self.config.rabbitmq.report_queue_name, ensure=True)
        exchange = await self.channel.get_exchange(self.config.rabbitmq.exchange_name + "_dlx", ensure=True)
        exchange_dlx = await self.channel.get_exchange(self.config.rabbitmq.exchange_name + "_dlx", ensure=True)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                msg_id = message.message_id

                if msg_id is None:
                    
                    if not await try_retry(exchange, message, self.config):
                        await exchange_dlx.publish(
                            aio_pika.Message(body=message.body, 
                                             delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                             message_id="unknown_id"),
                            routing_key=self.config.rabbitmq.report_queue_name + "_dlx"
                        )

                        

                        await self.logger.info(operation="report_generation_failed", message=f'msg_id: unknown_id, error: Missing message_id')

                    continue

                try:

                    report = await self.report_repository.get_by_uuid(report_uuid=UUID(msg_id))

                    if isinstance(report, Exception):
                        raise report
                    
                    if report.status != entities.ReportStatus.PENDING:
                        await message.ack()
                        continue

                    await self.report_interactor.execute()

                    await message.ack()
                    await self.logger.info(operation="report_generation_success", message=msg_id)

                except Exception as e:
                    if not await try_retry(exchange, message, self.config):
                        
                        await exchange_dlx.publish(
                            aio_pika.Message(body=message.body, 
                                             delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                             message_id=msg_id),
                            routing_key=self.config.rabbitmq.report_queue_name + "_dlx"
                        )

                        exc = await self.report_repository.update(report_uuid=UUID(msg_id), data={"status": entities.ReportStatus.FAILED})

                        if isinstance(exc, Exception):
                            await self.logger.info(operation="report_status_update_failed", message=f'msg_id: {msg_id}, error: {str(e)}, details: Cant update report status to FAILED after exhausting retries')


                        await self.logger.info(operation="report_generation_failed", message=f'msg_id: {msg_id}, error: {str(e)}')

                        
                    







