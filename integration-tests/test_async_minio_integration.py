"""Integration tests for AsyncMinioService.

Tests async MinIO service operations against a real MinIO instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import tempfile
import uuid
from pathlib import Path

import pytest

from lvrgd.common.services.minio.async_minio_service import AsyncMinioService


class TestAsyncMinioIntegration:
    """Integration tests for AsyncMinioService."""

    @pytest.mark.asyncio
    async def test_minio_connection_and_health_check(
        self,
        async_minio_service: AsyncMinioService,
    ) -> None:
        """Test async MinIO connection and health check functionality."""
        # Verify connection by getting bucket list
        buckets = await async_minio_service.health_check()
        assert isinstance(buckets, list)

        # Test list_buckets method
        bucket_list = await async_minio_service.list_buckets()
        assert isinstance(bucket_list, list)
        assert bucket_list == buckets

    @pytest.mark.asyncio
    async def test_bucket_operations(self, async_minio_service: AsyncMinioService) -> None:
        """Test bucket creation, listing, verification, and cleanup."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"

        try:
            # Verify bucket doesn't exist initially
            assert not await async_minio_service.bucket_exists(test_bucket)

            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Verify bucket now exists
            assert await async_minio_service.bucket_exists(test_bucket)

            # Verify bucket appears in list
            buckets = await async_minio_service.list_buckets()
            assert test_bucket in buckets

        finally:
            # Cleanup: remove bucket
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_file_upload_download(self, async_minio_service: AsyncMinioService) -> None:
        """Test async file upload and download operations."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-file-{uuid.uuid4().hex}.txt"
        test_content = b"Integration test file content"

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as upload_file:
                upload_file.write(test_content)
                upload_path = upload_file.name

            # Upload file
            result_object = await async_minio_service.upload_file(
                object_name=object_name,
                file_path=upload_path,
                bucket_name=test_bucket,
            )
            assert result_object == object_name

            # Download file
            download_path = tempfile.mktemp()
            await async_minio_service.download_file(
                object_name=object_name,
                file_path=download_path,
                bucket_name=test_bucket,
            )

            # Verify content matches
            downloaded_content = Path(download_path).read_bytes()
            assert downloaded_content == test_content

        finally:
            # Cleanup
            Path(upload_path).unlink(missing_ok=True)
            Path(download_path).unlink(missing_ok=True)
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_object(test_bucket, object_name)
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_data_upload_download(self, async_minio_service: AsyncMinioService) -> None:
        """Test async data upload and download using bytes."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-data-{uuid.uuid4().hex}.bin"
        test_data = b"Binary data for integration testing"

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Upload data
            result_object = await async_minio_service.upload_data(
                object_name=object_name,
                data=test_data,
                bucket_name=test_bucket,
            )
            assert result_object == object_name

            # Download data
            downloaded_data = await async_minio_service.download_data(
                object_name=object_name,
                bucket_name=test_bucket,
            )

            # Verify data integrity
            assert downloaded_data == test_data

        finally:
            # Cleanup
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_object(test_bucket, object_name)
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_object_listing(self, async_minio_service: AsyncMinioService) -> None:
        """Test async object listing with prefix filtering."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        prefix = f"test-prefix-{uuid.uuid4().hex[:4]}"
        object_1 = f"{prefix}/object1.txt"
        object_2 = f"{prefix}/object2.txt"
        object_3 = "other/object3.txt"

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Upload multiple objects
            await async_minio_service.upload_data(object_1, b"data1", bucket_name=test_bucket)
            await async_minio_service.upload_data(object_2, b"data2", bucket_name=test_bucket)
            await async_minio_service.upload_data(object_3, b"data3", bucket_name=test_bucket)

            # List all objects
            all_objects = await async_minio_service.list_objects(bucket_name=test_bucket)
            assert len(all_objects) >= 3

            # List objects with prefix filter
            filtered_objects = await async_minio_service.list_objects(
                bucket_name=test_bucket,
                prefix=prefix,
            )
            assert len(filtered_objects) == 2
            assert object_1 in filtered_objects
            assert object_2 in filtered_objects
            assert object_3 not in filtered_objects

        finally:
            # Cleanup
            if await async_minio_service.bucket_exists(test_bucket):
                for obj in [object_1, object_2, object_3]:
                    async_minio_service.client.remove_object(test_bucket, obj)
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_object_deletion(self, async_minio_service: AsyncMinioService) -> None:
        """Test async object deletion operations."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-delete-{uuid.uuid4().hex}.txt"

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Upload object
            await async_minio_service.upload_data(
                object_name, b"delete me", bucket_name=test_bucket
            )

            # Verify object exists
            objects = await async_minio_service.list_objects(bucket_name=test_bucket)
            assert object_name in objects

            # Delete object
            await async_minio_service.remove_object(object_name, bucket_name=test_bucket)

            # Verify object is removed
            objects_after = await async_minio_service.list_objects(bucket_name=test_bucket)
            assert object_name not in objects_after

        finally:
            # Cleanup
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_presigned_url_generation(
        self,
        async_minio_service: AsyncMinioService,
    ) -> None:
        """Test async presigned URL generation."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-presigned-{uuid.uuid4().hex}.txt"

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Upload object
            await async_minio_service.upload_data(
                object_name, b"presigned url test", bucket_name=test_bucket
            )

            # Generate presigned URL
            url = await async_minio_service.generate_presigned_url(
                object_name=object_name,
                bucket_name=test_bucket,
            )

            # Verify URL format
            assert isinstance(url, str)
            assert len(url) > 0
            assert test_bucket in url
            assert object_name in url

        finally:
            # Cleanup
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_object(test_bucket, object_name)
                async_minio_service.client.remove_bucket(test_bucket)

    @pytest.mark.asyncio
    async def test_object_metadata(self, async_minio_service: AsyncMinioService) -> None:
        """Test async object metadata upload and retrieval."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-metadata-{uuid.uuid4().hex}.txt"
        test_metadata = {
            "custom-key": "custom-value",
            "author": "integration-test",
        }

        try:
            # Create bucket
            await async_minio_service.ensure_bucket(test_bucket)

            # Upload object with metadata
            await async_minio_service.upload_data(
                object_name=object_name,
                data=b"metadata test content",
                bucket_name=test_bucket,
                metadata=test_metadata,
            )

            # Retrieve object metadata
            stat = await async_minio_service.stat_object(
                object_name=object_name,
                bucket_name=test_bucket,
            )

            # Verify metadata (MinIO prefixes custom metadata with "x-amz-meta-")
            assert stat is not None
            assert hasattr(stat, "metadata")
            for key, value in test_metadata.items():
                amz_key = f"x-amz-meta-{key}"
                assert amz_key in stat.metadata
                assert stat.metadata[amz_key] == value

        finally:
            # Cleanup
            if await async_minio_service.bucket_exists(test_bucket):
                async_minio_service.client.remove_object(test_bucket, object_name)
                async_minio_service.client.remove_bucket(test_bucket)
