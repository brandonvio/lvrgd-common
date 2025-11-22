"""Custom exceptions for DynamoDB operations.

This module provides domain-specific exceptions for DynamoDB service operations
with rich context for debugging.
"""

from typing import Any


class DynamoDBServiceError(Exception):
    """Base exception for DynamoDB service errors.

    Provides context about the operation, partition key, and sort key.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        pk: str | None = None,
        sk: str | None = None,
    ) -> None:
        """Initialize DynamoDBServiceError.

        Args:
            message: Error message
            operation: Operation that failed
            pk: Partition key (if applicable)
            sk: Sort key (if applicable)
        """
        self.operation = operation
        self.pk = pk
        self.sk = sk
        super().__init__(message)


class DynamoDBBatchOperationError(DynamoDBServiceError):
    """Exception for batch operation failures.

    Includes information about failed items and successful count.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        failed_items: list[dict[str, Any]],
        successful_count: int,
    ) -> None:
        """Initialize DynamoDBBatchOperationError.

        Args:
            message: Error message
            operation: Operation that failed
            failed_items: List of items that failed to process
            successful_count: Number of successfully processed items
        """
        self.failed_items = failed_items
        self.successful_count = successful_count
        super().__init__(message, operation)


class DynamoDBTransactionError(DynamoDBServiceError):
    """Exception for transaction failures.

    Indicates that a transaction was cancelled or failed.
    """

    def __init__(self, message: str, operation: str) -> None:
        """Initialize DynamoDBTransactionError.

        Args:
            message: Error message
            operation: Operation that failed
        """
        super().__init__(message, operation)
