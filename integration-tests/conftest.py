"""Pytest fixtures for integration tests.

Loads environment variables and provides service fixtures for MinIO, MongoDB, and Redis.
"""

import os
from collections.abc import Iterator

import pytest
from dotenv import load_dotenv
from rich.console import Console

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.minio.minio_models import MinioConfig
from lvrgd.common.services.minio.minio_service import MinioService
from lvrgd.common.services.mongodb.mongodb_models import MongoConfig
from lvrgd.common.services.mongodb.mongodb_service import MongoService
from lvrgd.common.services.redis.redis_models import RedisConfig
from lvrgd.common.services.redis.redis_service import RedisService

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def logger() -> LoggingService:
    """Create a LoggingService instance for integration tests.

    Returns:
        LoggingService instance
    """
    console = Console()
    return LoggingService(console=console)


@pytest.fixture(scope="session")
def minio_config() -> MinioConfig:
    """Create MinIO configuration from environment variables.

    Returns:
        MinioConfig instance
    """
    return MinioConfig(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
        region=os.environ.get("MINIO_REGION"),
        default_bucket=os.environ.get("MINIO_BUCKET"),
    )


@pytest.fixture(scope="session")
def mongo_config() -> MongoConfig:
    """Create MongoDB configuration from environment variables.

    Returns:
        MongoConfig instance
    """
    host = os.environ["MONGODB_HOST"]
    port = os.environ["MONGODB_PORT"]
    database = os.environ["MONGODB_DATABASE"]
    username = os.environ.get("MONGODB_USERNAME")
    password = os.environ.get("MONGODB_PASSWORD")

    url = f"mongodb://{host}:{port}"

    return MongoConfig(
        url=url,
        database=database,
        username=username,
        password=password,
    )


@pytest.fixture(scope="session")
def redis_config() -> RedisConfig:
    """Create Redis configuration from environment variables.

    Returns:
        RedisConfig instance
    """
    return RedisConfig(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ.get("REDIS_PORT", "6379")),
        password=os.environ.get("REDIS_PASSWORD"),
    )


@pytest.fixture(scope="module")
def minio_service(logger: LoggingService, minio_config: MinioConfig) -> MinioService:
    """Create MinioService instance for integration tests.

    Args:
        logger: LoggingService instance
        minio_config: MinioConfig instance

    Returns:
        MinioService instance
    """
    return MinioService(logger=logger, config=minio_config)


@pytest.fixture(scope="module")
def mongo_service(logger: LoggingService, mongo_config: MongoConfig) -> Iterator[MongoService]:
    """Create MongoService instance for integration tests.

    Args:
        logger: LoggingService instance
        mongo_config: MongoConfig instance

    Yields:
        MongoService instance
    """
    service = MongoService(logger=logger, config=mongo_config)
    yield service
    service.close()


@pytest.fixture(scope="module")
def redis_service(logger: LoggingService, redis_config: RedisConfig) -> Iterator[RedisService]:
    """Create RedisService instance for integration tests.

    Args:
        logger: LoggingService instance
        redis_config: RedisConfig instance

    Yields:
        RedisService instance
    """
    service = RedisService(logger=logger, config=redis_config)
    yield service
    service.close()
