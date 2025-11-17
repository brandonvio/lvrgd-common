"""DynamoDB service for database operations using PynamoDB.

This module provides a simplified DynamoDB service implementation with:
- Strong typing for all operations
- CRUD operations (create, read, update, delete)
- Query operations by partition key and sort key with all comparison operators
- Batch operations for efficient reads and writes
"""

from typing import Any, TypeVar

from pynamodb.exceptions import DoesNotExist

from lvrgd.common.services.logging import LoggingService

from .dynamodb_exceptions import DynamoDBBatchOperationError, DynamoDBTransactionError
from .dynamodb_models import (
    DynamoDBBaseModel,
    DynamoDBConfig,
    PaginationResult,
    SortKeyCondition,
    TransactionWriteItem,
)

T = TypeVar("T", bound=DynamoDBBaseModel)


class DynamoDBService:
    """DynamoDB service for database operations."""

    def __init__(
        self,
        logger: LoggingService,
        config: DynamoDBConfig,
    ) -> None:
        """Initialize DynamoDBService with dependency injection.

        Args:
            logger: LoggingService instance for structured logging (REQUIRED)
            config: DynamoDB configuration model (REQUIRED)

        Note:
            All dependencies are REQUIRED with no Optional or default values.
            No boto3 clients created in constructor - PynamoDB handles connections.
        """
        self.log = logger
        self.config = config

        self.log.info(
            "Initialized DynamoDB service",
            table_name=config.table_name,
            region=config.region,
        )

    def save(self, item: DynamoDBBaseModel) -> None:
        """Save an item to DynamoDB (create or update).

        Model must be pre-configured with table_name and region before use.
        This method works for both creating new items and updating existing ones.

        Args:
            item: DynamoDB item model to save
        """
        self.log.info("Saving item to DynamoDB", pk=item.pk, sk=item.sk)
        item.save()

    def get_one(self, pk: str, sk: str, model_class: type[T]) -> T | None:
        """Retrieve a single item from DynamoDB.

        Model must be pre-configured with table_name and region before use.

        Args:
            pk: Partition key value
            sk: Sort key value
            model_class: PynamoDB model class to deserialize into

        Returns:
            Model instance if found, None otherwise
        """
        self.log.info("Getting item from DynamoDB", pk=pk, sk=sk)
        try:
            return model_class.get(pk, sk)
        except DoesNotExist:
            return None

    def delete(self, pk: str, sk: str, model_class: type[T]) -> None:
        """Delete an item from DynamoDB.

        Model must be pre-configured with table_name and region before use.

        Args:
            pk: Partition key value
            sk: Sort key value
            model_class: PynamoDB model class for table configuration

        Raises:
            DoesNotExist: If the item does not exist (fail-fast behavior)

        Note:
            This method intentionally fails if the item doesn't exist, following
            the fail-fast principle. If you need to delete only if exists, check
            with get_one() first.
        """
        self.log.info("Deleting item from DynamoDB", pk=pk, sk=sk)
        item = model_class.get(pk, sk)
        item.delete()

    def query_by_pk(
        self,
        pk: str,
        model_class: type[T],
        limit: int | None = None,
        last_evaluated_key: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> PaginationResult[T]:
        """Query items by partition key with pagination support.

        Model must be pre-configured with table_name and region before use.

        Args:
            pk: Partition key value to query
            model_class: PynamoDB model class to deserialize into
            limit: Maximum number of items to return
            last_evaluated_key: Continuation token from previous query
            index_name: Name of GSI or LSI to query (None for main table)

        Returns:
            PaginationResult with items, last_evaluated_key, and count
        """
        self.log.info("Querying items from DynamoDB", pk=pk, limit=limit, index_name=index_name)

        query_kwargs: dict[str, Any] = {}
        if limit is not None:
            query_kwargs["limit"] = limit
        if last_evaluated_key is not None:
            query_kwargs["last_evaluated_key"] = last_evaluated_key
        if index_name is not None:
            query_kwargs["index"] = index_name

        result_iterator = model_class.query(pk, **query_kwargs)
        items = list(result_iterator)

        # Extract last_evaluated_key from iterator if available
        pagination_key = getattr(result_iterator, "last_evaluated_key", None)

        return PaginationResult(
            items=items,
            last_evaluated_key=pagination_key,
            count=len(items),
        )

    def _build_range_key_condition(
        self,
        model_class: type[T],
        sk_condition: SortKeyCondition,
    ) -> Any:
        """Build PynamoDB range key condition from SortKeyCondition.

        Args:
            model_class: PynamoDB model class
            sk_condition: Sort key condition specification

        Returns:
            PynamoDB condition expression
        """
        operator_map = {
            "eq": lambda: model_class.sk == sk_condition.value,
            "ne": lambda: model_class.sk != sk_condition.value,
            "lt": lambda: model_class.sk < sk_condition.value,
            "le": lambda: model_class.sk <= sk_condition.value,
            "gt": lambda: model_class.sk > sk_condition.value,
            "ge": lambda: model_class.sk >= sk_condition.value,
            "begins_with": lambda: model_class.sk.startswith(sk_condition.value),
            "between": lambda: model_class.sk.between(
                sk_condition.lower_bound,
                sk_condition.upper_bound,
            ),
        }
        return operator_map[sk_condition.operator]()

    def query_by_pk_and_sk(
        self,
        pk: str,
        sk_condition: SortKeyCondition,
        model_class: type[T],
        limit: int | None = None,
        last_evaluated_key: dict[str, Any] | None = None,
        index_name: str | None = None,
    ) -> PaginationResult[T]:
        """Query items by partition key and sort key condition with pagination support.

        Model must be pre-configured with table_name and region before use.

        Args:
            pk: Partition key value to query
            sk_condition: Sort key condition with operator and value(s)
            model_class: PynamoDB model class to deserialize into
            limit: Maximum number of items to return
            last_evaluated_key: Continuation token from previous query
            index_name: Name of GSI or LSI to query (None for main table)

        Returns:
            PaginationResult with items, last_evaluated_key, and count
        """
        self.log.info(
            "Querying items from DynamoDB with sort key condition",
            pk=pk,
            operator=sk_condition.operator,
            limit=limit,
            index_name=index_name,
        )

        range_key_condition = self._build_range_key_condition(model_class, sk_condition)

        query_kwargs: dict[str, Any] = {"range_key_condition": range_key_condition}
        if limit is not None:
            query_kwargs["limit"] = limit
        if last_evaluated_key is not None:
            query_kwargs["last_evaluated_key"] = last_evaluated_key
        if index_name is not None:
            query_kwargs["index"] = index_name

        result_iterator = model_class.query(pk, **query_kwargs)
        items = list(result_iterator)

        # Extract last_evaluated_key from iterator if available
        pagination_key = getattr(result_iterator, "last_evaluated_key", None)

        return PaginationResult(
            items=items,
            last_evaluated_key=pagination_key,
            count=len(items),
        )

    def batch_get(
        self,
        keys: list[tuple[str, str]],
        model_class: type[T],
    ) -> list[T]:
        """Retrieve multiple items with automatic chunking at 25-item limit.

        Model must be pre-configured with table_name and region before use.
        Automatically splits large requests into 25-item chunks (DynamoDB limit).

        Args:
            keys: List of (pk, sk) tuples to retrieve
            model_class: PynamoDB model class for table configuration

        Returns:
            List of model instances (items that exist)

        Raises:
            DynamoDBBatchOperationError: If any chunk fails
        """
        self.log.info("Batch getting items from DynamoDB", count=len(keys))

        if not keys:
            return []

        # Split into 25-item chunks (DynamoDB limit)
        chunk_size = 25
        chunks = [keys[i : i + chunk_size] for i in range(0, len(keys), chunk_size)]
        all_results: list[T] = []
        processed_count = 0

        try:
            for chunk in chunks:
                chunk_results = list(model_class.batch_get(chunk))
                all_results.extend(chunk_results)
                processed_count += len(chunk)
        except Exception as e:
            failed_count = len(keys) - processed_count
            raise DynamoDBBatchOperationError(
                message=f"Batch get operation failed: {e}",
                operation="batch_get",
                processed_count=processed_count,
                failed_count=failed_count,
                details={"total_keys": len(keys), "chunk_size": chunk_size},
            ) from e

        return all_results

    def batch_write(self, items: list[DynamoDBBaseModel]) -> None:
        """Write multiple items with automatic chunking at 25-item limit.

        Model must be pre-configured with table_name and region before use.
        Automatically splits large requests into 25-item chunks (DynamoDB limit).

        Args:
            items: List of DynamoDB item models to write

        Raises:
            DynamoDBBatchOperationError: If any chunk fails
        """
        self.log.info("Batch writing items to DynamoDB", count=len(items))
        if not items:
            return

        model_class = type(items[0])
        chunk_size = 25
        chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
        processed_count = 0

        try:
            for chunk in chunks:
                with model_class.batch_write() as batch:
                    for item in chunk:
                        batch.save(item)
                processed_count += len(chunk)
        except Exception as e:
            failed_count = len(items) - processed_count
            raise DynamoDBBatchOperationError(
                message=f"Batch write operation failed: {e}",
                operation="batch_write",
                processed_count=processed_count,
                failed_count=failed_count,
                details={"total_items": len(items), "chunk_size": chunk_size},
            ) from e

    def transact_write(self, operations: list[TransactionWriteItem]) -> None:
        """Execute atomic multi-item write transaction.

        Model must be pre-configured with table_name and region before use.
        All operations succeed or all fail together.

        Args:
            operations: List of transaction write operations

        Raises:
            DynamoDBTransactionError: If transaction fails
        """
        self.log.info("Executing DynamoDB write transaction", operation_count=len(operations))

        if not operations:
            return

        # PynamoDB doesn't have built-in transaction support yet
        # This is a simplified implementation that would need to use boto3 directly
        # For now, raise not implemented to follow fail-fast principle
        raise DynamoDBTransactionError(
            message="Transaction write not yet implemented - requires boto3 integration",
            operation="transact_write",
            details={"operation_count": len(operations)},
        )

    def transact_get(
        self,
        keys: list[tuple[str, str]],
        model_class: type[T],  # noqa: ARG002
    ) -> list[T]:
        """Execute atomic multi-item read transaction.

        Model must be pre-configured with table_name and region before use.
        Returns all items or fails transaction.

        Args:
            keys: List of (pk, sk) tuples to retrieve atomically
            model_class: PynamoDB model class for table configuration

        Returns:
            List of model instances (all or nothing)

        Raises:
            DynamoDBTransactionError: If transaction fails

        Note:
            model_class parameter not currently used but required for API signature.
        """
        self.log.info("Executing DynamoDB read transaction", key_count=len(keys))

        if not keys:
            return []

        # PynamoDB doesn't have built-in transaction support yet
        # This is a simplified implementation that would need to use boto3 directly
        # For now, raise not implemented to follow fail-fast principle
        raise DynamoDBTransactionError(
            message="Transaction get not yet implemented - requires boto3 integration",
            operation="transact_get",
            details={"key_count": len(keys)},
        )
