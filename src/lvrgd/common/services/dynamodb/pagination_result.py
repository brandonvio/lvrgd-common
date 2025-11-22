"""Pagination result models for DynamoDB queries.

This module provides generic pagination results for DynamoDB query operations.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .dynamodb_base_model import DynamoDBBaseModel

T = TypeVar("T", bound=DynamoDBBaseModel)


class PaginationResult(BaseModel, Generic[T]):
    """Generic pagination result for DynamoDB queries.

    Preserves type safety through query operations by using Generic[T].
    """

    items: list[T] = Field(default_factory=list, description="List of items returned")
    last_evaluated_key: dict[str, Any] | None = Field(
        None, description="Last evaluated key for pagination"
    )
    count: int = Field(0, description="Number of items returned")

    model_config = ConfigDict(arbitrary_types_allowed=True)
