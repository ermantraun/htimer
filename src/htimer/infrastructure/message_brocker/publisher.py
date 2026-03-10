import aio_pika
from config import Config
from application import common_interfaces, common_exceptions



class Publisher(common_interfaces.JobGateway):
    def __init__(self, channel: aio_pika.abc.AbstractChannel, exchange: aio_pika.abc.ExchangeType, config: Config, logger: common_interfaces.Logger):
        self.channel = channel
        self.config = config.rabbitmq
        self.logger = logger



    async def publish_report(self, report_id: str) -> common_exceptions.JobGatewayError | None:
        try:
            exchange = await self.channel.get_exchange(self.config.exchange_name, ensure=True)


            await exchange.publish(
                aio_pika.Message(body=report_id.encode(), 
                                 delivery_mode=aio_pika.DeliveryMode.PERSISTENT, 
                                 message_id=report_id, headers=
                                 {"x-retry-count": self.config.retry_count}),
                routing_key=self.config.report_queue_name
            )


            return None

        
        except Exception as e:
            await self.logger.info(operation="publish_message_failed", message=report_id)
            return common_exceptions.JobGatewayError(str(e))