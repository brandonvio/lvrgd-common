"""MongoDB configuration models for database connections.

This module provides Pydantic models for configuring MongoDB connections
with validation and sensible defaults for production use.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MongoConfig(BaseModel):
    """MongoDB configuration model."""

    url: str = Field(
        ...,
        description="MongoDB connection URL (e.g., mongodb://localhost:27017)",
        examples=["mongodb://localhost:27017", "mongodb+srv://cluster.mongodb.net"],
    )
    database: str = Field(
        ..., description="Database name to connect to", examples=["myapp", "production"]
    )
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    max_pool_size: int = Field(
        100,
        description="Maximum number of connections in the connection pool",
        ge=1,
        le=500,
    )
    min_pool_size: int = Field(
        0,
        description="Minimum number of connections in the connection pool",
        ge=0,
        le=100,
    )
    server_selection_timeout_ms: int = Field(
        30000,
        description="Server selection timeout in milliseconds",
        ge=1000,
        le=120000,
    )
    connect_timeout_ms: int = Field(
        10000, description="Connection timeout in milliseconds", ge=1000, le=60000
    )
    retry_writes: bool = Field(True, description="Enable retryable writes")
    retry_reads: bool = Field(True, description="Enable retryable reads")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate MongoDB URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("URL must start with mongodb:// or mongodb+srv://")
        return v

    @field_validator("database")
    @classmethod
    def validate_database(cls, v: str) -> str:
        """Validate database name."""
        if not v or v.strip() == "":
            raise ValueError("Database name cannot be empty")
        # MongoDB database name restrictions
        invalid_chars = [" ", ".", "$", "/", "\\", "\0"]
        if any(char in v for char in invalid_chars):
            raise ValueError(
                f"Database name cannot contain: {', '.join(invalid_chars)}"
            )
        if len(v) > 64:
            raise ValueError("Database name cannot be longer than 64 characters")
        return v

    @field_validator("min_pool_size")
    @classmethod
    def validate_min_pool_size(cls, v: int, info) -> int:
        """Validate min_pool_size is less than max_pool_size."""
        if "max_pool_size" in info.data and v > info.data["max_pool_size"]:
            raise ValueError("min_pool_size cannot be greater than max_pool_size")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "mongodb://localhost:27017",
                "database": "myapp",
                "username": "appuser",
                "password": "secure_password",
                "max_pool_size": 100,
                "min_pool_size": 10,
                "server_selection_timeout_ms": 30000,
                "connect_timeout_ms": 10000,
                "retry_writes": True,
                "retry_reads": True,
            }
        }
    )
