from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGGER_")

    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ClockConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLOCK_")

    timezone: str = "UTC"

# -------------------- Postgres --------------------
class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    sync_driver: str = "postgresql+psycopg"
    async_driver: str = "postgresql+psycopg"
    host: str = "localhost"
    port: int = 5432
    user: str = "admin"
    password: str = "899595"
    db: str = "htimer"
    debug: bool = False

class HostInfoConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOST_INFO_")

    host_name: str = "localhost"
    http_secure: bool = False

class SecureConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SECURE_")

    secret_key: str = "your_secret_key"
    hash_method: str = "sha256"

# -------------------- FastAPI --------------------
class FastApiConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FASTAPI_")

    title: str = "Videoscop"
    version: str = "1.0"
    description: str = "Videoscop API"
    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


# -------------------- JWT --------------------
class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")
    algorithm: str = 'HS256'
    secret_key: str = "default"
    expiration_days: int = 30


# -------------------- MinIO --------------------
class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINIO_")

    access_key: str = 'YhHA9P9tsiMLuJnVIwes'
    secret_key: str = 'Zrr3xg6nrSpd3plpPFB3Bjj3iSAeml7kzzhni9bU'
    bucket_name: str = 'htimer-files'
    host: str = "127.0.0.1"
    port: int = 9000


class RabbitMQConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    exchange_name: str = "htimer_exchange"
    report_queue_name: str = "report_queue"
    heartbeat: int = 60
    blocked_connection_timeout: int = 30
    connection_attempts: int = 3
    retry_delay: int = 5
    socket_timeout: int = 30
    prefetch_count: int = 1
    retry_count: int = 3
    


class YooKassaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YOOKASSA_")

    shop_id: str = "your_shop_id"
    secret_key: str = "your_secret_key"
    confirmation_uri: str = "/payment/confirmation"

# -------------------- Root config --------------------
class Config(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    fastapi: FastApiConfig = FastApiConfig()
    jwt: JWTConfig = JWTConfig()
    minio: MinioConfig = MinioConfig()
    yookassa: YooKassaConfig = YooKassaConfig()
    clock_config: ClockConfig = ClockConfig()
    logger_config: LoggerConfig = LoggerConfig()
    host_info: HostInfoConfig = HostInfoConfig()
    secure_config: SecureConfig = SecureConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()