"""Simplified MinIO service for object storage operations."""

from __future__ import annotations

import io
import logging
from datetime import timedelta
from typing import Any

from minio import Minio
from minio.error import S3Error

from .minio_models import MinioConfig

# Error messages
ERROR_BUCKET_REQUIRED = (
    "Bucket name must be provided when no default bucket is configured"
)


class MinioService:
    """High-level wrapper around the official MinIO Python client."""

    def __init__(self, logger: logging.Logger, config: MinioConfig) -> None:
        """Create a new MinioService instance."""
        self.log = logger
        self.config = config

        self.log.info("Initializing MinIO client for endpoint: %s", config.endpoint)

        try:
            self._client = Minio(
                config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                session_token=config.session_token,
                secure=config.secure,
                region=config.region,
            )

            if config.default_bucket:
                if config.auto_create_bucket:
                    self.ensure_bucket(config.default_bucket)
                else:
                    self.log.debug(
                        "Using configured default bucket: %s",
                        config.default_bucket,
                    )

        except Exception:
            self.log.exception("Failed to initialize MinIO client")
            raise

    @property
    def client(self) -> Minio:
        """Expose the underlying MinIO client for advanced operations."""
        return self._client

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _resolve_bucket(self, bucket_name: str | None) -> str:
        """Resolve a bucket name using the configured default when necessary."""
        if bucket_name:
            return bucket_name
        if self.config.default_bucket:
            return self.config.default_bucket
        raise ValueError(ERROR_BUCKET_REQUIRED)

    # ------------------------------------------------------------------
    # Health checks and bucket operations
    # ------------------------------------------------------------------
    def health_check(self) -> list[str]:
        """Return the list of accessible buckets, verifying connectivity."""
        try:
            buckets = self._client.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            self.log.debug("Successfully listed %d bucket(s)", len(bucket_names))
            return bucket_names
        except S3Error:
            self.log.exception("MinIO health check failed")
            raise

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check whether a bucket exists."""
        self.log.debug("Checking if bucket exists: %s", bucket_name)
        exists = self._client.bucket_exists(bucket_name)
        self.log.info("Bucket %s exists: %s", bucket_name, exists)
        return exists

    def ensure_bucket(self, bucket_name: str) -> None:
        """Ensure the provided bucket exists, creating it when necessary."""
        if self.bucket_exists(bucket_name):
            return

        self.log.info("Creating bucket: %s", bucket_name)
        self._client.make_bucket(bucket_name, location=self.config.region)
        self.log.info("Bucket created successfully: %s", bucket_name)

    def list_buckets(self) -> list[str]:
        """List all buckets available to the credentials."""
        self.log.debug("Listing buckets")
        buckets = self._client.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        self.log.info("Found %d bucket(s)", len(bucket_names))
        return bucket_names

    # ------------------------------------------------------------------
    # Object operations
    # ------------------------------------------------------------------
    def upload_file(
        self,
        object_name: str,
        file_path: str,
        *,
        bucket_name: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload a file from disk to the specified bucket."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Uploading file '%s' to bucket '%s' as object '%s'",
            file_path,
            resolved_bucket,
            object_name,
        )
        result = self._client.fput_object(
            resolved_bucket,
            object_name,
            file_path,
            content_type=content_type,
            metadata=metadata,
        )
        self.log.info(
            "Uploaded file '%s' to bucket '%s' (etag=%s)",
            object_name,
            resolved_bucket,
            result.etag,
        )
        return result.object_name

    def download_file(
        self,
        object_name: str,
        file_path: str,
        *,
        bucket_name: str | None = None,
    ) -> None:
        """Download an object from MinIO and store it on disk."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Downloading object '%s' from bucket '%s' to '%s'",
            object_name,
            resolved_bucket,
            file_path,
        )
        self._client.fget_object(resolved_bucket, object_name, file_path)
        self.log.info(
            "Downloaded object '%s' from bucket '%s' to '%s'",
            object_name,
            resolved_bucket,
            file_path,
        )

    def upload_data(
        self,
        object_name: str,
        data: bytes,
        *,
        bucket_name: str | None = None,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload raw bytes to MinIO without touching the filesystem."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        data_stream = io.BytesIO(data)
        length = len(data)
        self.log.debug(
            "Uploading %d bytes to bucket '%s' as object '%s'",
            length,
            resolved_bucket,
            object_name,
        )
        result = self._client.put_object(
            resolved_bucket,
            object_name,
            data_stream,
            length,
            content_type=content_type,
            metadata=metadata,
        )
        self.log.info(
            "Uploaded %d bytes to bucket '%s' (etag=%s)",
            length,
            resolved_bucket,
            result.etag,
        )
        return result.object_name

    def download_data(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> bytes:
        """Download an object's contents directly into memory."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Downloading object '%s' from bucket '%s' into memory",
            object_name,
            resolved_bucket,
        )
        response = self._client.get_object(resolved_bucket, object_name)
        try:
            data = response.read()
            self.log.info(
                "Downloaded object '%s' from bucket '%s' (%d bytes)",
                object_name,
                resolved_bucket,
                len(data),
            )
            return data
        finally:
            response.close()
            response.release_conn()

    def list_objects(
        self,
        *,
        bucket_name: str | None = None,
        prefix: str | None = None,
        recursive: bool = True,
    ) -> list[str]:
        """List objects in a bucket, returning their names."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Listing objects in bucket '%s' (prefix=%s, recursive=%s)",
            resolved_bucket,
            prefix,
            recursive,
        )
        objects = self._client.list_objects(
            resolved_bucket,
            prefix=prefix,
            recursive=recursive,
        )
        object_names = [obj.object_name for obj in objects]
        self.log.info(
            "Found %d object(s) in bucket '%s'",
            len(object_names),
            resolved_bucket,
        )
        return object_names

    def remove_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> None:
        """Remove a single object from a bucket."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Removing object '%s' from bucket '%s'",
            object_name,
            resolved_bucket,
        )
        self._client.remove_object(resolved_bucket, object_name)
        self.log.info(
            "Removed object '%s' from bucket '%s'",
            object_name,
            resolved_bucket,
        )

    def generate_presigned_url(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
        method: str = "GET",
        expires: timedelta = timedelta(minutes=15),
        response_headers: dict[str, str] | None = None,
        request_params: dict[str, Any] | None = None,
    ) -> str:
        """Generate a presigned URL for accessing an object."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Generating presigned URL for object '%s' (method=%s, expires=%s)",
            object_name,
            method,
            expires,
        )
        url = self._client.get_presigned_url(
            method,
            resolved_bucket,
            object_name,
            expires=expires,
            response_headers=response_headers,
            request_params=request_params,
        )
        self.log.info("Generated presigned URL for object '%s'", object_name)
        return url

    def stat_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> Any:
        """Retrieve metadata about an object."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Fetching metadata for object '%s' in bucket '%s'",
            object_name,
            resolved_bucket,
        )
        metadata = self._client.stat_object(resolved_bucket, object_name)
        self.log.info(
            "Fetched metadata for object '%s' in bucket '%s'",
            object_name,
            resolved_bucket,
        )
        return metadata
