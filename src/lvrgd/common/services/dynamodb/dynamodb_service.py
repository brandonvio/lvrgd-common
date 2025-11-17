"""DynamoDB service for database operations.

This module provides a boto3-based DynamoDB service implementation with:
- Strong typing for all operations via boto3-stubs
- CRUD, query, batch, and transaction operations
- Structured logging
- Repository pattern (pure Pydantic DTOs + service layer)
"""

import time
from typing import TYPE_CHECKING, Any, TypeVar

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

from lvrgd.common.exceptions.dynamodb_exceptions import (
    DynamoDBBatchOperationError,
    DynamoDBServiceError,
    DynamoDBTransactionError,
)
from lvrgd.common.services.logging import LoggingService

from .dynamodb_base_model import DynamoDBBaseModel
from .dynamodb_config import DynamoDBConfig
from .pagination_result import PaginationResult
from .sort_key_condition import SortKeyCondition
from .transaction_write_item import TransactionWriteItem

T = TypeVar("T", bound=DynamoDBBaseModel)


class DynamoDBService:
    """DynamoDB service for database operations using Repository Pattern.

    Provides CRUD, query, batch, and transaction operations with strong type safety.
    All dependencies are injected via constructor (no Optional, no defaults).
    """

    def __init__(self, logger: LoggingService, config: DynamoDBConfig) -> None:
        """Initialize DynamoDBService with injected dependencies.

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

        # Create boto3 resource and table internally (NOT injected)
        session_kwargs: dict[str, Any] = {"region_name": config.region}

        if config.aws_access_key_id:
            session_kwargs["aws_access_key_id"] = config.aws_access_key_id
        if config.aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = config.aws_secret_access_key

        dynamodb = boto3.resource("dynamodb", **session_kwargs)

        # Create table resource with optional endpoint_url
        if config.endpoint_url:
            dynamodb = boto3.resource(
                "dynamodb", endpoint_url=config.endpoint_url, **session_kwargs
            )

        self._table: Table = dynamodb.Table(config.table_name)

    def _build_key_condition_expression(self, sk_condition: SortKeyCondition) -> Any:
        """Build boto3 Key condition expression from SortKeyCondition.

        Args:
            sk_condition: Sort key condition model

        Returns:
            boto3 Key condition expression
        """
        sk_key = Key("sk")

        if sk_condition.operator == "eq":
            return sk_key.eq(sk_condition.value)
        if sk_condition.operator == "lt":
            return sk_key.lt(sk_condition.value)
        if sk_condition.operator == "le":
            return sk_key.lte(sk_condition.value)
        if sk_condition.operator == "gt":
            return sk_key.gt(sk_condition.value)
        if sk_condition.operator == "ge":
            return sk_key.gte(sk_condition.value)
        if sk_condition.operator == "begins_with":
            return sk_key.begins_with(sk_condition.value)
        if sk_condition.operator == "between":
            return sk_key.between(sk_condition.value, sk_condition.value2)

        # This should never happen due to Literal type
        error_msg = f"Unsupported operator: {sk_condition.operator}"
        raise ValueError(error_msg)

    def save(self, item: DynamoDBBaseModel) -> None:
        """Save item to DynamoDB.

        Args:
            item: Item to save

        Raises:
            DynamoDBServiceError: If save operation fails
        """
        start_time = time.time()
        self.log.info("Saving item", pk=item.pk, sk=item.sk)

        try:
            self._table.put_item(Item=item.model_dump())
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info("Item saved successfully", pk=item.pk, sk=item.sk, elapsed_ms=elapsed_ms)
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to save item",
                pk=item.pk,
                sk=item.sk,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to save item: {e}",
                operation="save",
                pk=item.pk,
                sk=item.sk,
            ) from e

    def get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None:
        """Get single item from DynamoDB.

        Args:
            pk: Partition key
            sk: Sort key
            model_class: Pydantic model class to deserialize into

        Returns:
            Deserialized item or None if not found

        Raises:
            DynamoDBServiceError: If get operation fails
        """
        start_time = time.time()
        self.log.info("Getting item", pk=pk, sk=sk)

        try:
            response = self._table.get_item(Key={"pk": pk, "sk": sk})
            elapsed_ms = int((time.time() - start_time) * 1000)

            if "Item" not in response:
                self.log.info("Item not found", pk=pk, sk=sk, elapsed_ms=elapsed_ms)
                return None

            item = model_class(**response["Item"])
            self.log.info("Item retrieved successfully", pk=pk, sk=sk, elapsed_ms=elapsed_ms)
            return item
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error("Failed to get item", pk=pk, sk=sk, error=str(e), elapsed_ms=elapsed_ms)
            raise DynamoDBServiceError(
                f"Failed to get item: {e}",
                operation="get_one",
                pk=pk,
                sk=sk,
            ) from e

    def delete(self, pk: str, sk: str) -> None:
        """Delete item from DynamoDB.

        Args:
            pk: Partition key
            sk: Sort key

        Raises:
            DynamoDBServiceError: If delete operation fails
        """
        start_time = time.time()
        self.log.info("Deleting item", pk=pk, sk=sk)

        try:
            self._table.delete_item(Key={"pk": pk, "sk": sk})
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info("Item deleted successfully", pk=pk, sk=sk, elapsed_ms=elapsed_ms)
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to delete item",
                pk=pk,
                sk=sk,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to delete item: {e}",
                operation="delete",
                pk=pk,
                sk=sk,
            ) from e

    def update(self, pk: str, sk: str, updates: dict[str, Any]) -> None:
        """Update item in DynamoDB.

        Args:
            pk: Partition key
            sk: Sort key
            updates: Dictionary of field updates

        Raises:
            DynamoDBServiceError: If update operation fails
        """
        start_time = time.time()
        self.log.info("Updating item", pk=pk, sk=sk, update_count=len(updates))

        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}

            for idx, (key, value) in enumerate(updates.items()):
                placeholder_name = f"#attr{idx}"
                placeholder_value = f":val{idx}"
                update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
                expression_attribute_names[placeholder_name] = key
                expression_attribute_values[placeholder_value] = value

            update_expression = "SET " + ", ".join(update_expression_parts)

            self._table.update_item(
                Key={"pk": pk, "sk": sk},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info("Item updated successfully", pk=pk, sk=sk, elapsed_ms=elapsed_ms)
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to update item",
                pk=pk,
                sk=sk,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to update item: {e}",
                operation="update",
                pk=pk,
                sk=sk,
            ) from e

    def query_by_pk(
        self,
        pk: str,
        model_class: type[T],
        limit: int | None = None,
        last_evaluated_key: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> PaginationResult[T]:
        """Query items by partition key.

        Args:
            pk: Partition key
            model_class: Pydantic model class to deserialize into
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query
            index_name: Name of GSI/LSI to query

        Returns:
            Pagination result with items and metadata

        Raises:
            DynamoDBServiceError: If query operation fails
        """
        start_time = time.time()
        self.log.info("Querying by partition key", pk=pk, index_name=index_name)

        try:
            query_params: dict[str, Any] = {
                "KeyConditionExpression": Key("pk").eq(pk),
            }

            if limit:
                query_params["Limit"] = limit
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            if index_name:
                query_params["IndexName"] = index_name

            response = self._table.query(**query_params)

            items = [model_class(**item) for item in response.get("Items", [])]
            result = PaginationResult(
                items=items,
                last_evaluated_key=response.get("LastEvaluatedKey"),
                count=len(items),
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Query completed",
                pk=pk,
                count=result.count,
                has_more=result.last_evaluated_key is not None,
                elapsed_ms=elapsed_ms,
            )
            return result
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error("Failed to query by pk", pk=pk, error=str(e), elapsed_ms=elapsed_ms)
            raise DynamoDBServiceError(
                f"Failed to query by pk: {e}",
                operation="query_by_pk",
                pk=pk,
            ) from e

    def query_by_pk_and_sk(
        self,
        pk: str,
        sk_condition: SortKeyCondition,
        model_class: type[T],
        limit: int | None = None,
        last_evaluated_key: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> PaginationResult[T]:
        """Query items by partition key and sort key condition.

        Args:
            pk: Partition key
            sk_condition: Sort key condition (supports all 8 operators)
            model_class: Pydantic model class to deserialize into
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token from previous query
            index_name: Name of GSI/LSI to query

        Returns:
            Pagination result with items and metadata

        Raises:
            DynamoDBServiceError: If query operation fails
        """
        start_time = time.time()
        self.log.info(
            "Querying by pk and sk condition",
            pk=pk,
            operator=sk_condition.operator,
            index_name=index_name,
        )

        try:
            # Build key condition expression
            pk_condition = Key("pk").eq(pk)
            sk_key_condition = self._build_key_condition_expression(sk_condition)
            key_condition = pk_condition & sk_key_condition

            query_params: dict[str, Any] = {
                "KeyConditionExpression": key_condition,
            }

            if limit:
                query_params["Limit"] = limit
            if last_evaluated_key:
                query_params["ExclusiveStartKey"] = last_evaluated_key
            if index_name:
                query_params["IndexName"] = index_name

            response = self._table.query(**query_params)

            items = [model_class(**item) for item in response.get("Items", [])]
            result = PaginationResult(
                items=items,
                last_evaluated_key=response.get("LastEvaluatedKey"),
                count=len(items),
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Query completed",
                pk=pk,
                operator=sk_condition.operator,
                count=result.count,
                has_more=result.last_evaluated_key is not None,
                elapsed_ms=elapsed_ms,
            )
            return result
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to query by pk and sk",
                pk=pk,
                operator=sk_condition.operator,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to query by pk and sk: {e}",
                operation="query_by_pk_and_sk",
                pk=pk,
            ) from e

    def batch_get(self, keys: list[tuple[str, str]], model_class: type[T]) -> list[T]:
        """Batch retrieve items from DynamoDB.

        Args:
            keys: List of (pk, sk) tuples
            model_class: Pydantic model class to deserialize into

        Returns:
            List of deserialized items

        Raises:
            DynamoDBServiceError: If batch get operation fails
        """
        start_time = time.time()
        self.log.info("Batch get operation", key_count=len(keys))

        try:
            all_items = []

            # Chunk keys into batches of 100 (DynamoDB limit)
            for i in range(0, len(keys), 100):
                chunk = keys[i : i + 100]
                batch_keys = [{"pk": pk, "sk": sk} for pk, sk in chunk]

                response = self._table.meta.client.batch_get_item(
                    RequestItems={
                        self.config.table_name: {
                            "Keys": batch_keys,
                        }
                    }
                )

                items_data = response.get("Responses", {}).get(self.config.table_name, [])
                items = [model_class(**item) for item in items_data]
                all_items.extend(items)

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Batch get completed",
                requested=len(keys),
                retrieved=len(all_items),
                elapsed_ms=elapsed_ms,
            )
            return all_items
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to batch get items",
                key_count=len(keys),
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to batch get items: {e}",
                operation="batch_get",
            ) from e

    def batch_write(self, items: list[DynamoDBBaseModel]) -> None:
        """Batch write items to DynamoDB.

        Args:
            items: List of items to write

        Raises:
            DynamoDBBatchOperationError: If batch write fails
        """
        start_time = time.time()
        self.log.info("Batch write operation", item_count=len(items))

        try:
            successful_count = 0
            failed_items = []

            # Chunk items into batches of 25 (DynamoDB limit)
            for i in range(0, len(items), 25):
                chunk = items[i : i + 25]
                request_items = [{"PutRequest": {"Item": item.model_dump()}} for item in chunk]

                response = self._table.meta.client.batch_write_item(
                    RequestItems={self.config.table_name: request_items}
                )

                # Check for unprocessed items
                unprocessed = response.get("UnprocessedItems", {}).get(self.config.table_name, [])

                successful_count += len(chunk) - len(unprocessed)
                failed_items.extend(unprocessed)

            if failed_items:
                elapsed_ms = int((time.time() - start_time) * 1000)
                self.log.error(
                    "Batch write partially failed",
                    successful=successful_count,
                    failed=len(failed_items),
                    elapsed_ms=elapsed_ms,
                )
                raise DynamoDBBatchOperationError(
                    f"Batch write failed for {len(failed_items)} items",
                    operation="batch_write",
                    failed_items=failed_items,
                    successful_count=successful_count,
                )

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Batch write completed",
                item_count=len(items),
                successful=successful_count,
                elapsed_ms=elapsed_ms,
            )
        except DynamoDBBatchOperationError:
            raise
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Failed to batch write items",
                item_count=len(items),
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBServiceError(
                f"Failed to batch write items: {e}",
                operation="batch_write",
            ) from e

    def transact_write(self, operations: list[TransactionWriteItem]) -> None:
        """Execute transaction write operations atomically.

        Args:
            operations: List of transaction write operations

        Raises:
            DynamoDBTransactionError: If transaction fails
        """
        start_time = time.time()
        operation_types = [op.operation for op in operations]
        self.log.info(
            "Transaction write operation", operation_count=len(operations), types=operation_types
        )

        try:
            transact_items = []

            for op in operations:
                if op.operation == "put":
                    transact_items.append(
                        {"Put": {"TableName": self.config.table_name, "Item": op.item.model_dump()}}
                    )
                elif op.operation == "update":
                    # Build update expression
                    update_expression_parts = []
                    expression_attribute_names = {}
                    expression_attribute_values = {}

                    for idx, (key, value) in enumerate(op.updates.items()):
                        placeholder_name = f"#attr{idx}"
                        placeholder_value = f":val{idx}"
                        update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
                        expression_attribute_names[placeholder_name] = key
                        expression_attribute_values[placeholder_value] = value

                    update_expression = "SET " + ", ".join(update_expression_parts)

                    transact_items.append(
                        {
                            "Update": {
                                "TableName": self.config.table_name,
                                "Key": {"pk": op.pk, "sk": op.sk},
                                "UpdateExpression": update_expression,
                                "ExpressionAttributeNames": expression_attribute_names,
                                "ExpressionAttributeValues": expression_attribute_values,
                            }
                        }
                    )
                elif op.operation == "delete":
                    transact_items.append(
                        {
                            "Delete": {
                                "TableName": self.config.table_name,
                                "Key": {"pk": op.pk, "sk": op.sk},
                            }
                        }
                    )

            self._table.meta.client.transact_write_items(TransactItems=transact_items)

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Transaction write completed",
                operation_count=len(operations),
                elapsed_ms=elapsed_ms,
            )
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Transaction write failed",
                operation_count=len(operations),
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBTransactionError(
                f"Transaction write failed: {e}",
                operation="transact_write",
            ) from e

    def transact_get(self, keys: list[tuple[str, str]], model_class: type[T]) -> list[T]:
        """Execute transaction get operations atomically.

        Args:
            keys: List of (pk, sk) tuples
            model_class: Pydantic model class to deserialize into

        Returns:
            List of deserialized items

        Raises:
            DynamoDBTransactionError: If transaction fails
        """
        start_time = time.time()
        self.log.info("Transaction get operation", key_count=len(keys))

        try:
            transact_items = [
                {"Get": {"TableName": self.config.table_name, "Key": {"pk": pk, "sk": sk}}}
                for pk, sk in keys
            ]

            response = self._table.meta.client.transact_get_items(TransactItems=transact_items)

            items = [
                model_class(**item["Item"])
                for item in response.get("Responses", [])
                if "Item" in item
            ]

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info(
                "Transaction get completed",
                requested=len(keys),
                retrieved=len(items),
                elapsed_ms=elapsed_ms,
            )
            return items
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error(
                "Transaction get failed",
                key_count=len(keys),
                error=str(e),
                elapsed_ms=elapsed_ms,
            )
            raise DynamoDBTransactionError(
                f"Transaction get failed: {e}",
                operation="transact_get",
            ) from e

    def ping(self) -> bool:
        """Health check for DynamoDB connection.

        Returns:
            True if connection is healthy

        Raises:
            DynamoDBServiceError: If ping fails
        """
        start_time = time.time()
        self.log.info("Pinging DynamoDB")

        try:
            self._table.load()
            table_status = self._table.table_status

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info("Ping successful", table_status=table_status, elapsed_ms=elapsed_ms)
            return True
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error("Ping failed", error=str(e), elapsed_ms=elapsed_ms)
            raise DynamoDBServiceError(
                f"Ping failed: {e}",
                operation="ping",
            ) from e

    def count(self, pk: str, sk_condition: SortKeyCondition | None = None) -> int:
        """Count items matching query.

        Args:
            pk: Partition key
            sk_condition: Optional sort key condition

        Returns:
            Count of matching items

        Raises:
            DynamoDBServiceError: If count operation fails
        """
        start_time = time.time()
        self.log.info("Counting items", pk=pk, has_sk_condition=sk_condition is not None)

        try:
            query_params: dict[str, Any] = {
                "Select": "COUNT",
            }

            if sk_condition:
                pk_condition = Key("pk").eq(pk)
                sk_key_condition = self._build_key_condition_expression(sk_condition)
                key_condition = pk_condition & sk_key_condition
                query_params["KeyConditionExpression"] = key_condition
            else:
                query_params["KeyConditionExpression"] = Key("pk").eq(pk)

            response = self._table.query(**query_params)
            count = response.get("Count", 0)

            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.info("Count completed", pk=pk, count=count, elapsed_ms=elapsed_ms)
            return count
        except ClientError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.log.error("Count failed", pk=pk, error=str(e), elapsed_ms=elapsed_ms)
            raise DynamoDBServiceError(
                f"Count failed: {e}",
                operation="count",
                pk=pk,
            ) from e
