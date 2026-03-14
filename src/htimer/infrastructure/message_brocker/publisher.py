from uuid import UUID

import aio_pika

from htimer.application import common_exceptions, common_interfaces
from htimer.config import Config


class Publisher(common_interfaces.JobGateway):
    def __init__(
        self,
        channel: aio_pika.abc.AbstractChannel,
        exchange: aio_pika.abc.ExchangeType,
        config: Config,
        logger: common_interfaces.Logger,
    ):
        self.channel = channel
        self.config = config.rabbitmq
        self.logger = logger

    async def publish_report(
        self, report_id: UUID
    ) -> common_exceptions.JobGatewayError | None:
        try:
            exchange = await self.channel.get_exchange(
                self.config.exchange_name, ensure=True
            )

            await exchange.publish(
                aio_pika.Message(
                    body=str(report_id).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(report_id),
                    headers={"x-retry-count": self.config.retry_count},
                ),
                routing_key=self.config.report_queue_name,
            )

            return None

        except Exception as e:
            await self.logger.info(
                operation="publish_message_failed", message=str(report_id)
            )
            return common_exceptions.JobGatewayError(f"Ошибка шлюза задач: {e}")
