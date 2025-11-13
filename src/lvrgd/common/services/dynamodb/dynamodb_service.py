"""DynamoDB service for database operations using boto3.

This module provides a simplified DynamoDB service implementation with:
- Strong typing for all operations
- CRUD operations (create, read, update, delete)
- Query operations by partition key
- Health check functionality
"""

from typing import Any, TypeVar

import boto3
from botocore.exceptions import ClientError

from lvrgd.common.services.logging import LoggingService

from .dynamodb_models import DynamoDBBaseModel, DynamoDBConfig

T = TypeVar("T", bound=DynamoDBBaseModel)


class DynamoDBService:
    """DynamoDB service for database operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: DynamoDBConfig,
    ) -> None:
        """Initialize DynamoDBService.

        Args:
            logger: LoggingService instance for structured logging (REQUIRED)
            config: DynamoDB configuration model (REQUIRED)
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initializing DynamoDB connection",
            table_name=config.table_name,
            region=config.region,
        )

        # Build boto3 client configuration
        client_config: dict[str, Any] = {"region_name": config.region}

        if config.endpoint_url:
            client_config["endpoint_url"] = config.endpoint_url
        if config.aws_access_key_id:
            client_config["aws_access_key_id"] = config.aws_access_key_id
        if config.aws_secret_access_key:
            client_config["aws_secret_access_key"] = config.aws_secret_access_key

        # Initialize DynamoDB client
        self._client = boto3.client("dynamodb", **client_config)
        self._resource = boto3.resource("dynamodb", **client_config)
        self._table = self._resource.Table(config.table_name)

        # Verify connection
        if not self.ping():
            msg = f"Failed to connect to DynamoDB table {self.config.table_name}"
            self.log.error(msg)
            raise ConnectionError(msg)
        self.log.info("Successfully connected to DynamoDB")

    def ping(self) -> bool:
        """Verify DynamoDB connectivity with health check.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            self._client.describe_table(TableName=self.config.table_name)
        except ClientError:
            self.log.exception("DynamoDB health check failed")
            return False
        else:
            return True

    def create(self, item: DynamoDBBaseModel) -> None:
        """Create a new item in DynamoDB.

        Args:
            item: DynamoDB item model to create

        Raises:
            ClientError: If the operation fails
        """
        self.log.info("Creating item in DynamoDB", pk=item.pk, sk=item.sk)
        self._table.put_item(Item=item.model_dump())

    def update(self, item: DynamoDBBaseModel) -> None:
        """Update an existing item in DynamoDB.

        Args:
            item: DynamoDB item model to update

        Raises:
            ClientError: If the operation fails
        """
        self.log.info("Updating item in DynamoDB", pk=item.pk, sk=item.sk)
        self._table.put_item(Item=item.model_dump())

    def get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None:
        """Retrieve a single item from DynamoDB.

        Args:
            pk: Partition key value
            sk: Sort key value
            model_class: Pydantic model class to deserialize into

        Returns:
            Deserialized model instance if found, None otherwise

        Raises:
            ClientError: If the operation fails
        """
        self.log.info("Getting item from DynamoDB", pk=pk, sk=sk)
        response = self._table.get_item(Key={"pk": pk, "sk": sk})

        item = response.get("Item")
        if item is None:
            return None

        return model_class.model_validate(item)

    def query_by_pk(
        self,
        pk: str,
        model_class: type[T],
    ) -> list[T]:
        """Query items by partition key.

        Args:
            pk: Partition key value to query
            model_class: Pydantic model class to deserialize into

        Returns:
            List of deserialized model instances

        Raises:
            ClientError: If the operation fails
        """
        self.log.info("Querying items from DynamoDB", pk=pk)

        query_params: dict[str, Any] = {
            "KeyConditionExpression": "pk = :pk",
            "ExpressionAttributeValues": {":pk": pk},
        }

        response = self._table.query(**query_params)
        items = response.get("Items", [])

        return [model_class.model_validate(item) for item in items]

    def close(self) -> None:
        """Close DynamoDB connection and cleanup resources."""
        self.log.info("Closing DynamoDB connection")
        # boto3 client handles cleanup automatically
