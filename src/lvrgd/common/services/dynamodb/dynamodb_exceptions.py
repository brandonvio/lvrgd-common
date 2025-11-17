"""Custom exception classes for DynamoDB service operations.

This module provides structured exception classes for DynamoDB operations:
- Base exception with operation context
- Batch operation exceptions with detailed error tracking
- Transaction exceptions with cancellation reasons
"""

from typing import Any


class DynamoDBServiceError(Exception):
    """Base exception for all DynamoDB service errors.

    Provides structured error context including operation details.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize DynamoDB service error.

        Args:
            message: Human-readable error message
            operation: DynamoDB operation that failed (e.g., 'batch_get', 'query')
            details: Additional error context as structured data
        """
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.details = details or {}

    def __str__(self) -> str:
        """Return formatted error message with operation context."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (operation={self.operation}, {detail_str})"
        return f"{self.message} (operation={self.operation})"


class DynamoDBBatchOperationError(DynamoDBServiceError):
    """Exception for batch operation failures.

    Provides detailed tracking of processed vs failed items.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        processed_count: int,
        failed_count: int,
        unprocessed_items: list[Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize batch operation error.

        Args:
            message: Human-readable error message
            operation: Batch operation that failed ('batch_get' or 'batch_write')
            processed_count: Number of items successfully processed
            failed_count: Number of items that failed
            unprocessed_items: List of items that were not processed
            details: Additional error context
        """
        super().__init__(message, operation, details)
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.unprocessed_items = unprocessed_items or []

    def __str__(self) -> str:
        """Return formatted error message with batch operation details."""
        batch_info = f"processed={self.processed_count}, failed={self.failed_count}"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (operation={self.operation}, {batch_info}, {detail_str})"
        return f"{self.message} (operation={self.operation}, {batch_info})"


class DynamoDBTransactionError(DynamoDBServiceError):
    """Exception for transaction operation failures.

    Provides cancellation reasons from failed transactions.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        cancellation_reasons: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize transaction error.

        Args:
            message: Human-readable error message
            operation: Transaction operation that failed ('transact_write' or 'transact_get')
            cancellation_reasons: List of reasons why transaction was cancelled
            details: Additional error context
        """
        super().__init__(message, operation, details)
        self.cancellation_reasons = cancellation_reasons or []

    def __str__(self) -> str:
        """Return formatted error message with transaction cancellation details."""
        reason_count = len(self.cancellation_reasons)
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (operation={self.operation}, cancellation_reasons={reason_count}, {detail_str})"
        return f"{self.message} (operation={self.operation}, cancellation_reasons={reason_count})"
