import pika
from config import Config





class MessageBrokerInitializer:
    def __init__(self, config: Config):
        self.config = config
    
    def init(self) -> None:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.rabbitmq.host,
                port=self.config.rabbitmq.port,
                credentials=pika.PlainCredentials(
                    username=self.config.rabbitmq.username,
                    password=self.config.rabbitmq.password
                ),
                heartbeat=self.config.rabbitmq.heartbeat,
                blocked_connection_timeout=self.config.rabbitmq.blocked_connection_timeout,
                connection_attempts=self.config.rabbitmq.connection_attempts,
                retry_delay=self.config.rabbitmq.retry_delay,
                socket_timeout=self.config.rabbitmq.socket_timeout
            )
        )

        channel = connection.channel()

        channel.queue_declare( #type: ignore[call-arg]
            queue=self.config.rabbitmq.report_queue_name,
            durable=True
        )
        channel.exchange_declare( #type: ignore[call-arg]
            exchange=self.config.rabbitmq.exchange_name,
            exchange_type="direct",
            durable=True
        )
        channel.queue_bind( #type: ignore[call-arg]
            queue=self.config.rabbitmq.report_queue_name,
            exchange=self.config.rabbitmq.exchange_name,
            routing_key=self.config.rabbitmq.report_queue_name
        )

        channel.queue_declare( #type: ignore[call-arg]
            queue=self.config.rabbitmq.report_queue_name + "_ttl",
            durable=True,
            arguments={
                "x-message-ttl": 30 * 60 * 1000,
                "x-dead-letter-exchange": self.config.rabbitmq.exchange_name,
                "x-dead-letter-routing-key": self.config.rabbitmq.report_queue_name,
                "x-overflow": "drop-head",
            },
        )

        channel.exchange_declare( #type: ignore[call-arg]
            exchange=self.config.rabbitmq.exchange_name + "_dlx",
            exchange_type="direct",
            durable=True
        )
        channel.queue_declare( #type: ignore[call-arg]
            queue=self.config.rabbitmq.report_queue_name + "_dlq",
            durable=True
        )
        channel.queue_bind( #type: ignore[call-arg]
            queue=self.config.rabbitmq.report_queue_name + "_dlq",
            exchange=self.config.rabbitmq.exchange_name + "_dlx",
            routing_key=self.config.rabbitmq.report_queue_name + "_dlq"
        )

