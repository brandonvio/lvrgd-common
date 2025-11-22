"""Sort key condition models for DynamoDB queries.

This module provides type-safe sort key query conditions for DynamoDB operations.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SortKeyCondition(BaseModel):
    """Type-safe sort key condition for DynamoDB queries.

    Supports all DynamoDB sort key comparison operators with validation.
    """

    operator: Literal["eq", "lt", "le", "gt", "ge", "begins_with", "between"] = Field(
        ..., description="Comparison operator"
    )
    value: str = Field(..., description="Primary comparison value")
    value2: str | None = Field(None, description="Secondary value for 'between' operator")

    @model_validator(mode="after")
    def validate_between_operator(self) -> "SortKeyCondition":
        """Validate that 'between' operator has value2 set."""
        if self.operator == "between" and self.value2 is None:
            raise ValueError("'between' operator requires value2 to be set")
        return self
