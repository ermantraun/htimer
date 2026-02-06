from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    secret_key: str = "default"
    expiration_days: int = 30


# -------------------- MinIO --------------------
class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINIO_")

    user: str = "minioadmin"
    password: str = "minioadmin"
    host: str = "127.0.0.1"
    port: int = 9000
    expiration_days: int = 30


# -------------------- Root config --------------------
class Config(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    fastapi: FastApiConfig = FastApiConfig()
    jwt: JWTConfig = JWTConfig()
    minio: MinioConfig = MinioConfig()
