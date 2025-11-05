"""MinIO service package providing high-level object storage utilities."""

from .minio_models import MinioConfig
from .minio_service import MinioService

__all__ = ["MinioConfig", "MinioService"]
