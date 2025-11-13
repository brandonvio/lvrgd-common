"""DynamoDB configuration models and base model for items.

This module provides Pydantic models for configuring DynamoDB connections
and a base model for DynamoDB items with pk and sk support.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Error messages
ERROR_EMPTY_TABLE_NAME = "Table name cannot be empty"
ERROR_EMPTY_REGION = "Region cannot be empty"


class DynamoDBBaseModel(BaseModel):
    """Base model for all DynamoDB items with partition key and sort key.

    All DynamoDB items should inherit from this model to ensure
    consistent pk and sk fields.
    """

    pk: str = Field(..., description="Partition key for the item")
    sk: str = Field(..., description="Sort key for the item")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pk": "USER#12345",
                "sk": "PROFILE#main",
            },
        },
    )


class DynamoDBConfig(BaseModel):
    """DynamoDB configuration model."""

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
    aws_access_key_id: str | None = Field(
        None,
        description="AWS access key ID for authentication",
    )
    aws_secret_access_key: str | None = Field(
        None,
        description="AWS secret access key for authentication",
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
                "aws_access_key_id": "test",
                "aws_secret_access_key": "test",
            },
        },
    )
