"""DynamoDB configuration models.

This module provides Pydantic models for configuring DynamoDB connections
with validation for production use.
"""

from pydantic import BaseModel, Field


class DynamoDBConfig(BaseModel):
    """DynamoDB configuration model."""

    table_name: str = Field(..., description="DynamoDB table name", examples=["users", "orders"])
    region: str = Field(..., description="AWS region name", examples=["us-east-1", "us-west-2"])
    endpoint_url: str | None = Field(
        None,
        description="Custom endpoint URL for local DynamoDB",
        examples=["http://localhost:8000"],
    )
    aws_access_key_id: str | None = Field(None, description="AWS access key ID")
    aws_secret_access_key: str | None = Field(None, description="AWS secret access key")
