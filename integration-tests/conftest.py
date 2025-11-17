"""Pytest fixtures for integration tests.

Loads environment variables and provides service fixtures for MinIO, MongoDB, and Redis.
"""

import os
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from lvrgd.common.services import LoggingService
from lvrgd.common.services.dynamodb.dynamodb_config import DynamoDBConfig
from lvrgd.common.services.dynamodb.dynamodb_service import DynamoDBService
from lvrgd.common.services.minio.async_minio_service import AsyncMinioService
from lvrgd.common.services.minio.minio_models import MinioConfig
from lvrgd.common.services.minio.minio_service import MinioService
from lvrgd.common.services.mongodb.async_mongodb_service import AsyncMongoService
from lvrgd.common.services.mongodb.mongodb_models import MongoConfig
from lvrgd.common.services.mongodb.mongodb_service import MongoService
from lvrgd.common.services.redis.async_redis_service import AsyncRedisService
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
    return LoggingService()


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


@pytest.fixture(scope="session")
def dynamodb_config() -> DynamoDBConfig:
    """Create DynamoDB configuration from environment variables.

    Returns:
        DynamoDBConfig instance
    """
    table_name = os.environ.get("DYNAMODB_TABLE", "test-table")
    region = os.environ.get("AWS_REGION", "us-east-1")

    # Build endpoint URL from host and port
    dynamodb_host = os.environ.get("DYNAMODB_HOST")
    dynamodb_port = os.environ.get("DYNAMODB_PORT")
    endpoint_url = f"http://{dynamodb_host}:{dynamodb_port}" if dynamodb_host and dynamodb_port else None

    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY")
    aws_secret_access_key = os.environ.get("AWS_SECRET_KEY")

    return DynamoDBConfig(
        table_name=table_name,
        region=region,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
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
def async_minio_service(logger: LoggingService, minio_config: MinioConfig) -> AsyncMinioService:
    """Create AsyncMinioService instance for integration tests.

    Args:
        logger: LoggingService instance
        minio_config: MinioConfig instance

    Returns:
        AsyncMinioService instance
    """
    return AsyncMinioService(logger=logger, config=minio_config)


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


@pytest_asyncio.fixture
async def async_mongo_service(
    logger: LoggingService, mongo_config: MongoConfig
) -> AsyncIterator[AsyncMongoService]:
    """Create AsyncMongoService instance for integration tests.

    Args:
        logger: LoggingService instance
        mongo_config: MongoConfig instance

    Yields:
        AsyncMongoService instance
    """
    service = AsyncMongoService(logger=logger, config=mongo_config)
    yield service
    await service.close()


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


@pytest_asyncio.fixture
async def async_redis_service(
    logger: LoggingService, redis_config: RedisConfig
) -> AsyncIterator[AsyncRedisService]:
    """Create AsyncRedisService instance for integration tests.

    Args:
        logger: LoggingService instance
        redis_config: RedisConfig instance

    Yields:
        AsyncRedisService instance
    """
    service = AsyncRedisService(logger=logger, config=redis_config)
    yield service
    await service.close()


@pytest.fixture(scope="module")
def dynamodb_service(logger: LoggingService, dynamodb_config: DynamoDBConfig) -> Iterator[DynamoDBService]:
    """Create DynamoDBService instance and table for integration tests.

    Args:
        logger: LoggingService instance
        dynamodb_config: DynamoDBConfig instance

    Yields:
        DynamoDBService instance
    """
    import boto3

    # Create DynamoDB client for table management
    dynamodb_client = boto3.client(
        "dynamodb",
        region_name=dynamodb_config.region,
        endpoint_url=dynamodb_config.endpoint_url,
        aws_access_key_id=dynamodb_config.aws_access_key_id,
        aws_secret_access_key=dynamodb_config.aws_secret_access_key,
    )

    # Create table if it doesn't exist
    try:
        dynamodb_client.describe_table(TableName=dynamodb_config.table_name)
        logger.info("Table already exists", table_name=dynamodb_config.table_name)
    except dynamodb_client.exceptions.ResourceNotFoundException:
        logger.info("Creating test table", table_name=dynamodb_config.table_name)
        dynamodb_client.create_table(
            TableName=dynamodb_config.table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Wait for table to be active
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=dynamodb_config.table_name)

    service = DynamoDBService(logger=logger, config=dynamodb_config)
    yield service

    # Cleanup: Delete table after tests
    try:
        logger.info("Deleting test table", table_name=dynamodb_config.table_name)
        dynamodb_client.delete_table(TableName=dynamodb_config.table_name)
    except Exception as e:
        logger.warning("Failed to delete test table", error=str(e))
