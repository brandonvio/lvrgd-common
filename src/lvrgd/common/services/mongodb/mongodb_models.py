"""MongoDB configuration models for database connections.

This module provides Pydantic models for configuring MongoDB connections
with validation and sensible defaults for production use.
"""

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# Constants
MAX_DATABASE_NAME_LENGTH = 64

# Error messages
ERROR_INVALID_URL = "URL must start with mongodb:// or mongodb+srv://"
ERROR_EMPTY_DATABASE = "Database name cannot be empty"
ERROR_DATABASE_TOO_LONG = (
    f"Database name cannot be longer than {MAX_DATABASE_NAME_LENGTH} characters"
)
ERROR_MIN_POOL_SIZE = "min_pool_size cannot be greater than max_pool_size"


class MongoConfig(BaseModel):
    """MongoDB configuration model."""

    url: str = Field(
        ...,
        description="MongoDB connection URL (e.g., mongodb://localhost:27017)",
        examples=["mongodb://localhost:27017", "mongodb+srv://cluster.mongodb.net"],
    )
    database: str = Field(
        ...,
        description="Database name to connect to",
        examples=["myapp", "production"],
    )
    username: str | None = Field(None, description="Username for authentication")
    password: str | None = Field(None, description="Password for authentication")
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
        10000,
        description="Connection timeout in milliseconds",
        ge=1000,
        le=60000,
    )
    retry_writes: bool = Field(default=True, description="Enable retryable writes")
    retry_reads: bool = Field(default=True, description="Enable retryable reads")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate MongoDB URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(ERROR_INVALID_URL)
        return v

    @field_validator("database")
    @classmethod
    def validate_database(cls, v: str) -> str:
        """Validate database name."""
        if not v or v.strip() == "":
            raise ValueError(ERROR_EMPTY_DATABASE)
        # MongoDB database name restrictions
        invalid_chars = [" ", ".", "$", "/", "\\", "\0"]
        if any(char in v for char in invalid_chars):
            error_msg = f"Database name cannot contain: {', '.join(invalid_chars)}"
            raise ValueError(error_msg)
        if len(v) > MAX_DATABASE_NAME_LENGTH:
            raise ValueError(ERROR_DATABASE_TOO_LONG)
        return v

    @field_validator("min_pool_size")
    @classmethod
    def validate_min_pool_size(cls, v: int, info: ValidationInfo) -> int:
        """Validate min_pool_size is less than max_pool_size."""
        if "max_pool_size" in info.data and v > info.data["max_pool_size"]:
            raise ValueError(ERROR_MIN_POOL_SIZE)
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
            },
        },
    )
