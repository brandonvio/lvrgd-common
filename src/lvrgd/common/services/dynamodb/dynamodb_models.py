"""DynamoDB configuration models and base model for items.

This module provides Pydantic models for configuring DynamoDB connections
and a base model for DynamoDB items with pk and sk support.
"""

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pynamodb.attributes import UnicodeAttribute
from pynamodb.models import Model

T = TypeVar("T")

# Error messages
ERROR_EMPTY_TABLE_NAME = "Table name cannot be empty"
ERROR_EMPTY_REGION = "Region cannot be empty"


class PaginationResult(BaseModel, Generic[T]):
    """Pagination result for DynamoDB query operations.

    Wraps query results with pagination metadata including continuation token.
    """

    items: list[T] = Field(
        ...,
        description="List of items returned from query",
    )
    last_evaluated_key: dict[str, Any] | None = Field(
        None,
        description="Continuation token for next page of results",
    )
    count: int = Field(
        ...,
        description="Number of items in this result set",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TransactionWriteItem(BaseModel):
    """Transaction write item for atomic multi-item operations.

    Supports put, delete, and update operations with optional conditions.
    """

    operation: Literal["put", "delete", "update"] = Field(
        ...,
        description="Transaction operation type",
    )
    item: Any | None = Field(
        None,
        description="Item to put or update (required for put/update operations)",
    )
    key: tuple[str, str] | None = Field(
        None,
        description="(pk, sk) for delete operations",
    )
    condition_expression: str | None = Field(
        None,
        description="Optional condition expression for the operation",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_operation_fields(self) -> "TransactionWriteItem":
        """Validate required fields for each operation type."""
        if self.operation in ("put", "update") and self.item is None:
            msg = f"{self.operation} operation requires item field"
            raise ValueError(msg)
        if self.operation == "delete" and self.key is None:
            msg = "delete operation requires key field"
            raise ValueError(msg)
        return self


class SortKeyCondition(BaseModel):
    """Sort key condition for DynamoDB queries.

    Supports all DynamoDB comparison operators for sort key queries.
    """

    operator: Literal["eq", "ne", "lt", "le", "gt", "ge", "begins_with", "between"] = Field(
        ...,
        description="Comparison operator for sort key query",
    )
    value: str | None = Field(
        None,
        description="Value for single-value operators (eq, ne, lt, le, gt, ge, begins_with)",
    )
    lower_bound: str | None = Field(
        None,
        description="Lower bound value for between operator",
    )
    upper_bound: str | None = Field(
        None,
        description="Upper bound value for between operator",
    )

    @model_validator(mode="after")
    def validate_operator_fields(self) -> "SortKeyCondition":
        """Validate required fields for each operator type."""
        if self.operator == "between":
            if self.lower_bound is None or self.upper_bound is None:
                msg = "between operator requires both lower_bound and upper_bound"
                raise ValueError(msg)
        elif self.value is None:
            msg = f"{self.operator} operator requires value field"
            raise ValueError(msg)
        return self


class DynamoDBBaseModel(Model):
    """Base model for all DynamoDB items with partition key and sort key.

    All DynamoDB items should inherit from this model to ensure
    consistent pk and sk fields.
    """

    pk = UnicodeAttribute(hash_key=True)
    sk = UnicodeAttribute(range_key=True)

    class Meta:
        """PynamoDB Meta configuration."""

        table_name: str = ""
        region: str = "us-east-1"


class DynamoDBConfig(BaseModel):
    """DynamoDB configuration model.

    Simplified configuration - uses boto3 credential chain for AWS authentication.
    Credentials are discovered via environment variables, IAM roles, or ~/.aws/credentials.

    Note:
        This configuration is for the DynamoDBService instance. PynamoDB models must
        be pre-configured with table_name and region before passing to service methods.
        Set ModelClass.Meta.table_name and ModelClass.Meta.region at class definition
        or application startup.
    """

    table_name: str = Field(
        ...,
        description="DynamoDB table name",
        examples=["users", "transactions"],
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region for DynamoDB",
    )
    endpoint_url: str | None = Field(
        None,
        description="Custom endpoint URL for local DynamoDB",
        examples=["http://localhost:8000"],
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate table name is not empty."""
        if not v or v.strip() == "":
            raise ValueError(ERROR_EMPTY_TABLE_NAME)
        return v.strip()

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region is not empty."""
        if not v or v.strip() == "":
            raise ValueError(ERROR_EMPTY_REGION)
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "table_name": "users",
                "region": "us-east-1",
                "endpoint_url": "http://localhost:8000",
            },
        },
    )
