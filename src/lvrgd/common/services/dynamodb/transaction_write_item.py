"""Transaction write item models for DynamoDB operations.

This module provides type-safe transaction write operation models.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from .dynamodb_base_model import DynamoDBBaseModel


class TransactionWriteItem(BaseModel):
    """Type-safe transaction write operation model.

    Represents a single operation in a DynamoDB transaction.
    """

    operation: Literal["put", "update", "delete"] = Field(..., description="Operation type")
    item: DynamoDBBaseModel | None = Field(None, description="Item for put operations")
    pk: str | None = Field(None, description="Partition key for update/delete operations")
    sk: str | None = Field(None, description="Sort key for update/delete operations")
    updates: dict[str, Any] | None = Field(
        None, description="Update expressions for update operations"
    )
