"""Async MinIO service for object storage operations."""

from __future__ import annotations

import asyncio
import io
from datetime import timedelta
from typing import Any

from minio import Minio
from minio.error import S3Error

from lvrgd.common.services import LoggingService

from .minio_models import MinioConfig

# Error messages
ERROR_BUCKET_REQUIRED = "Bucket name must be provided when no default bucket is configured"


class AsyncMinioService:
    """Async wrapper around the official MinIO Python client using asyncio.to_thread."""

    def __init__(self, logger: LoggingService, config: MinioConfig) -> None:
        """Create a new AsyncMinioService instance.

        Args:
            logger: LoggingService instance for structured logging
            config: MinIO configuration model
        """
        self.log = logger
        self.config = config

        self.log.info("Initializing async MinIO client", endpoint=config.endpoint)

        try:
            self._client = Minio(
                config.endpoint,
                access_key=config.access_key,
                secret_key=config.secret_key,
                session_token=config.session_token,
                secure=config.secure,
                region=config.region,
            )

            self.log.debug("Async MinIO client initialized", endpoint=config.endpoint)

        except Exception:
            self.log.exception("Failed to initialize async MinIO client")
            raise

    async def _init_default_bucket(self) -> None:
        """Initialize default bucket if configured."""
        if self.config.default_bucket:
            if self.config.auto_create_bucket:
                await self.ensure_bucket(self.config.default_bucket)
            else:
                self.log.debug(
                    "Using configured default bucket",
                    bucket=self.config.default_bucket,
                )

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
    async def health_check(self) -> list[str]:
        """Return the list of accessible buckets, verifying connectivity."""
        try:
            buckets = await asyncio.to_thread(self._client.list_buckets)
        except S3Error:
            self.log.exception("Async MinIO health check failed")
            raise
        else:
            bucket_names = [bucket.name for bucket in buckets]
            self.log.debug("Successfully listed buckets", count=len(bucket_names))
            return bucket_names

    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check whether a bucket exists."""
        self.log.debug("Checking if bucket exists", bucket=bucket_name)
        exists = await asyncio.to_thread(self._client.bucket_exists, bucket_name)
        self.log.info("Bucket exists check", bucket=bucket_name, exists=exists)
        return exists

    async def ensure_bucket(self, bucket_name: str) -> None:
        """Ensure the provided bucket exists, creating it when necessary."""
        if await self.bucket_exists(bucket_name):
            return

        self.log.info("Creating bucket", bucket=bucket_name)
        await asyncio.to_thread(self._client.make_bucket, bucket_name, location=self.config.region)
        self.log.info("Bucket created successfully", bucket=bucket_name)

    async def list_buckets(self) -> list[str]:
        """List all buckets available to the credentials."""
        self.log.debug("Listing buckets")
        buckets = await asyncio.to_thread(self._client.list_buckets)
        bucket_names = [bucket.name for bucket in buckets]
        self.log.info("Found buckets", count=len(bucket_names))
        return bucket_names

    # ------------------------------------------------------------------
    # Object operations
    # ------------------------------------------------------------------
    async def upload_file(
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
            "Uploading file to bucket",
            file_path=file_path,
            bucket=resolved_bucket,
            object_name=object_name,
        )
        result = await asyncio.to_thread(
            self._client.fput_object,
            resolved_bucket,
            object_name,
            file_path,
            content_type=content_type,
            metadata=metadata,
        )
        self.log.info(
            "Uploaded file to bucket",
            object_name=object_name,
            bucket=resolved_bucket,
            etag=result.etag,
        )
        return result.object_name

    async def download_file(
        self,
        object_name: str,
        file_path: str,
        *,
        bucket_name: str | None = None,
    ) -> None:
        """Download an object from MinIO and store it on disk."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Downloading object from bucket",
            object_name=object_name,
            bucket=resolved_bucket,
            file_path=file_path,
        )
        await asyncio.to_thread(self._client.fget_object, resolved_bucket, object_name, file_path)
        self.log.info(
            "Downloaded object from bucket",
            object_name=object_name,
            bucket=resolved_bucket,
            file_path=file_path,
        )

    async def upload_data(
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
            "Uploading bytes to bucket",
            bytes=length,
            bucket=resolved_bucket,
            object_name=object_name,
        )
        result = await asyncio.to_thread(
            self._client.put_object,
            resolved_bucket,
            object_name,
            data_stream,
            length,
            content_type=content_type,
            metadata=metadata,
        )
        self.log.info(
            "Uploaded bytes to bucket",
            bytes=length,
            bucket=resolved_bucket,
            etag=result.etag,
        )
        return result.object_name

    async def download_data(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> bytes:
        """Download an object's contents directly into memory."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Downloading object into memory",
            object_name=object_name,
            bucket=resolved_bucket,
        )
        response = await asyncio.to_thread(self._client.get_object, resolved_bucket, object_name)
        try:
            data = response.read()
            self.log.info(
                "Downloaded object into memory",
                object_name=object_name,
                bucket=resolved_bucket,
                bytes=len(data),
            )
            return data
        finally:
            response.close()
            response.release_conn()

    async def list_objects(
        self,
        *,
        bucket_name: str | None = None,
        prefix: str | None = None,
        recursive: bool = True,
    ) -> list[str]:
        """List objects in a bucket, returning their names."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Listing objects in bucket",
            bucket=resolved_bucket,
            prefix=prefix,
            recursive=recursive,
        )
        # Collect objects inside thread to avoid blocking I/O on event loop
        objects = await asyncio.to_thread(
            lambda: list(
                self._client.list_objects(
                    resolved_bucket,
                    prefix=prefix,
                    recursive=recursive,
                )
            )
        )
        object_names = [obj.object_name for obj in objects]
        self.log.info(
            "Found objects in bucket",
            count=len(object_names),
            bucket=resolved_bucket,
        )
        return object_names

    async def remove_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> None:
        """Remove a single object from a bucket."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Removing object from bucket",
            object_name=object_name,
            bucket=resolved_bucket,
        )
        await asyncio.to_thread(self._client.remove_object, resolved_bucket, object_name)
        self.log.info(
            "Removed object from bucket",
            object_name=object_name,
            bucket=resolved_bucket,
        )

    async def generate_presigned_url(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
        method: str = "GET",
        expires: timedelta = timedelta(minutes=15),
        response_headers: dict[str, str] | None = None,
    ) -> str:
        """Generate a presigned URL for accessing an object."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Generating presigned URL for object",
            object_name=object_name,
            method=method,
            expires=str(expires),
        )
        url = await asyncio.to_thread(
            self._client.get_presigned_url,
            method,
            resolved_bucket,
            object_name,
            expires=expires,
            response_headers=response_headers,
        )
        self.log.info("Generated presigned URL for object", object_name=object_name)
        return url

    async def stat_object(
        self,
        object_name: str,
        *,
        bucket_name: str | None = None,
    ) -> Any:
        """Retrieve metadata about an object."""
        resolved_bucket = self._resolve_bucket(bucket_name)
        self.log.debug(
            "Fetching metadata for object",
            object_name=object_name,
            bucket=resolved_bucket,
        )
        metadata = await asyncio.to_thread(self._client.stat_object, resolved_bucket, object_name)
        self.log.info(
            "Fetched metadata for object",
            object_name=object_name,
            bucket=resolved_bucket,
        )
        return metadata
