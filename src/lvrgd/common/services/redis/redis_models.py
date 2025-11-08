"""Redis configuration models for database connections.

This module provides Pydantic models for configuring Redis connections
with validation and sensible defaults for production use.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants
MAX_DB_NUMBER = 15

# Error messages
ERROR_INVALID_HOST = "Host cannot be empty"
ERROR_INVALID_PORT = "Port must be between 1 and 65535"
ERROR_INVALID_DB = f"Database number must be between 0 and {MAX_DB_NUMBER}"
ERROR_NEGATIVE_TIMEOUT = "Timeout must be positive"
ERROR_NEGATIVE_MAX_CONNECTIONS = "Max connections must be positive"


class RedisConfig(BaseModel):
    """Redis configuration model."""

    host: str = Field(
        ...,
        description="Redis server host",
        examples=["localhost", "redis.example.com"],
    )
    port: int = Field(
        6379,
        description="Redis server port",
        ge=1,
        le=65535,
    )
    db: int = Field(
        0,
        description="Redis database number (0-15)",
        ge=0,
        le=MAX_DB_NUMBER,
    )
    password: str | None = Field(None, description="Password for authentication")
    username: str | None = Field(None, description="Username for authentication (Redis 6+)")
    socket_connect_timeout: int = Field(
        5,
        description="Socket connection timeout in seconds",
        ge=1,
        le=300,
    )
    socket_timeout: int = Field(
        5,
        description="Socket timeout in seconds",
        ge=1,
        le=300,
    )
    max_connections: int = Field(
        50,
        description="Maximum number of connections in the connection pool",
        ge=1,
        le=1000,
    )
    decode_responses: bool = Field(
        default=True,
        description="Decode responses from bytes to strings",
    )
    retry_on_timeout: bool = Field(
        default=True,
        description="Retry operations on timeout",
    )
    health_check_interval: int = Field(
        30,
        description="Health check interval in seconds",
        ge=0,
        le=300,
    )
    namespace: str | None = Field(
        None,
        description="Optional namespace prefix for all keys",
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate Redis host."""
        if not v or v.strip() == "":
            raise ValueError(ERROR_INVALID_HOST)
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": "secure_password",
                "username": "default",
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "max_connections": 50,
                "decode_responses": True,
                "retry_on_timeout": True,
                "health_check_interval": 30,
            },
        },
    )
