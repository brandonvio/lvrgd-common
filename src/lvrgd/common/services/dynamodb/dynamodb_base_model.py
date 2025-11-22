"""Base model for DynamoDB entities.

This module provides a pure Pydantic base model for DynamoDB entities with
partition key (pk) and sort key (sk) fields. All DynamoDB models should inherit
from this base.
"""

from pydantic import BaseModel, Field


class DynamoDBBaseModel(BaseModel):
    """Base model for DynamoDB entities with partition and sort keys.

    This is a pure DTO (Data Transfer Object) with no business logic or persistence
    methods. All domain models should inherit from this base to ensure pk/sk fields.
    """

    pk: str = Field(..., description="Partition key")
    sk: str = Field(..., description="Sort key")
