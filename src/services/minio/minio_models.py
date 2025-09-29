"""MinIO configuration models for object storage connections."""

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# Bucket naming constraints (matching AWS S3/MinIO rules)
MIN_BUCKET_NAME_LENGTH = 3
MAX_BUCKET_NAME_LENGTH = 63
ALLOWED_BUCKET_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-.")

# Error messages
ERROR_EMPTY_ENDPOINT = "Endpoint cannot be empty"
ERROR_EMPTY_ACCESS_KEY = "Access key cannot be empty"
ERROR_EMPTY_SECRET_KEY = "Secret key cannot be empty"
ERROR_INVALID_BUCKET_LENGTH = (
    f"Bucket name must be between {MIN_BUCKET_NAME_LENGTH} and "
    f"{MAX_BUCKET_NAME_LENGTH} characters long"
)
ERROR_BUCKET_INVALID_CHARS = (
    "Bucket name may only contain lowercase letters, numbers, '.' and '-'"
)
ERROR_BUCKET_START_END = (
    "Bucket name must start and end with a lowercase letter or number"
)


class MinioConfig(BaseModel):
    """Configuration model describing how to connect to a MinIO deployment."""

    endpoint: str = Field(
        ...,
        description="Hostname (and optional port) for the MinIO server",
        examples=["play.min.io", "minio.internal:9000"],
    )
    access_key: str = Field(
        ...,
        description="Access key used for authentication",
        examples=["Q3AM3UQ867SPQQA43P2F"],
    )
    secret_key: str = Field(
        ...,
        description="Secret key used for authentication",
        examples=["zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"],
    )
    secure: bool = Field(
        default=True,
        description="Whether to use HTTPS when communicating with the server",
    )
    region: str | None = Field(
        default=None,
        description="Optional region name used when creating buckets",
    )
    session_token: str | None = Field(
        default=None,
        description="Optional session token for temporary credentials",
    )
    default_bucket: str | None = Field(
        default=None,
        description="Default bucket name used for storage operations",
        examples=["application-data"],
    )
    auto_create_bucket: bool = Field(
        default=False,
        description="Create the default bucket automatically when initializing the service",
    )

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        """Ensure the endpoint value is not empty."""
        if not value or not value.strip():
            raise ValueError(ERROR_EMPTY_ENDPOINT)
        return value

    @field_validator("access_key")
    @classmethod
    def validate_access_key(cls, value: str) -> str:
        """Ensure the access key is provided."""
        if not value or not value.strip():
            raise ValueError(ERROR_EMPTY_ACCESS_KEY)
        return value

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Ensure the secret key is provided."""
        if not value or not value.strip():
            raise ValueError(ERROR_EMPTY_SECRET_KEY)
        return value

    @field_validator("default_bucket")
    @classmethod
    def validate_default_bucket(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        """Validate bucket naming rules when a default bucket is provided."""
        if value is None:
            return None

        bucket = value.strip()
        length = len(bucket)
        if length < MIN_BUCKET_NAME_LENGTH or length > MAX_BUCKET_NAME_LENGTH:
            raise ValueError(ERROR_INVALID_BUCKET_LENGTH)

        if not set(bucket).issubset(ALLOWED_BUCKET_CHARS):
            raise ValueError(ERROR_BUCKET_INVALID_CHARS)

        if bucket[0] not in ALLOWED_BUCKET_CHARS - {"-", "."} or bucket[-1] not in (
            ALLOWED_BUCKET_CHARS - {"-", "."}
        ):
            raise ValueError(ERROR_BUCKET_START_END)

        if ".." in bucket or ".-" in bucket or "-." in bucket:
            raise ValueError(ERROR_BUCKET_INVALID_CHARS)

        # Store the normalized bucket name back into the data to avoid repeated stripping
        info.data.setdefault("default_bucket", bucket)
        return bucket

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "play.min.io:9000",
                "access_key": "minio",
                "secret_key": "minio123",
                "secure": False,
                "region": "us-east-1",
                "default_bucket": "application-data",
                "auto_create_bucket": True,
            },
        }
    )
