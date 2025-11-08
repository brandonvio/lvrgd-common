"""Integration tests for MinIO service.

Tests MinIO service operations against a real MinIO instance.
Configuration loaded from environment variables via conftest.py fixtures.
"""

import tempfile
import uuid
from pathlib import Path

from lvrgd.common.services.minio.minio_service import MinioService


class TestMinioIntegration:
    """Integration tests for MinioService."""

    def test_minio_connection_and_health_check(self, minio_service: MinioService) -> None:
        """Test MinIO connection and health check functionality."""
        # Verify connection by getting bucket list
        buckets = minio_service.health_check()
        assert isinstance(buckets, list)

        # Test list_buckets method
        bucket_list = minio_service.list_buckets()
        assert isinstance(bucket_list, list)
        assert bucket_list == buckets

    def test_bucket_operations(self, minio_service: MinioService) -> None:
        """Test bucket creation, listing, verification, and cleanup."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"

        try:
            # Verify bucket doesn't exist initially
            assert not minio_service.bucket_exists(test_bucket)

            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Verify bucket now exists
            assert minio_service.bucket_exists(test_bucket)

            # Verify bucket appears in list
            buckets = minio_service.list_buckets()
            assert test_bucket in buckets

        finally:
            # Cleanup: remove bucket
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_bucket(test_bucket)

    def test_file_upload_download(self, minio_service: MinioService) -> None:
        """Test file upload and download operations."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-file-{uuid.uuid4().hex}.txt"
        test_content = b"Integration test file content"

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Create temporary file for upload
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as upload_file:
                upload_file.write(test_content)
                upload_path = upload_file.name

            # Upload file
            result_object = minio_service.upload_file(
                object_name=object_name,
                file_path=upload_path,
                bucket_name=test_bucket,
            )
            assert result_object == object_name

            # Download file
            download_path = tempfile.mktemp()
            minio_service.download_file(
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
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_object(test_bucket, object_name)
                minio_service.client.remove_bucket(test_bucket)

    def test_data_upload_download(self, minio_service: MinioService) -> None:
        """Test data upload and download using bytes."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-data-{uuid.uuid4().hex}.bin"
        test_data = b"Binary data for integration testing"

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Upload data
            result_object = minio_service.upload_data(
                object_name=object_name,
                data=test_data,
                bucket_name=test_bucket,
            )
            assert result_object == object_name

            # Download data
            downloaded_data = minio_service.download_data(
                object_name=object_name,
                bucket_name=test_bucket,
            )

            # Verify data integrity
            assert downloaded_data == test_data

        finally:
            # Cleanup
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_object(test_bucket, object_name)
                minio_service.client.remove_bucket(test_bucket)

    def test_object_listing(self, minio_service: MinioService) -> None:
        """Test object listing with prefix filtering."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        prefix = f"test-prefix-{uuid.uuid4().hex[:4]}"
        object_1 = f"{prefix}/object1.txt"
        object_2 = f"{prefix}/object2.txt"
        object_3 = "other/object3.txt"

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Upload multiple objects
            minio_service.upload_data(object_1, b"data1", bucket_name=test_bucket)
            minio_service.upload_data(object_2, b"data2", bucket_name=test_bucket)
            minio_service.upload_data(object_3, b"data3", bucket_name=test_bucket)

            # List all objects
            all_objects = minio_service.list_objects(bucket_name=test_bucket)
            assert len(all_objects) >= 3

            # List objects with prefix filter
            filtered_objects = minio_service.list_objects(
                bucket_name=test_bucket,
                prefix=prefix,
            )
            assert len(filtered_objects) == 2
            assert object_1 in filtered_objects
            assert object_2 in filtered_objects
            assert object_3 not in filtered_objects

        finally:
            # Cleanup
            if minio_service.bucket_exists(test_bucket):
                for obj in [object_1, object_2, object_3]:
                    minio_service.client.remove_object(test_bucket, obj)
                minio_service.client.remove_bucket(test_bucket)

    def test_object_deletion(self, minio_service: MinioService) -> None:
        """Test object deletion operations."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-delete-{uuid.uuid4().hex}.txt"

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Upload object
            minio_service.upload_data(object_name, b"delete me", bucket_name=test_bucket)

            # Verify object exists
            objects = minio_service.list_objects(bucket_name=test_bucket)
            assert object_name in objects

            # Delete object
            minio_service.remove_object(object_name, bucket_name=test_bucket)

            # Verify object is removed
            objects_after = minio_service.list_objects(bucket_name=test_bucket)
            assert object_name not in objects_after

        finally:
            # Cleanup
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_bucket(test_bucket)

    def test_presigned_url_generation(self, minio_service: MinioService) -> None:
        """Test presigned URL generation."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-presigned-{uuid.uuid4().hex}.txt"

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Upload object
            minio_service.upload_data(object_name, b"presigned url test", bucket_name=test_bucket)

            # Generate presigned URL
            url = minio_service.generate_presigned_url(
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
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_object(test_bucket, object_name)
                minio_service.client.remove_bucket(test_bucket)

    def test_object_metadata(self, minio_service: MinioService) -> None:
        """Test object metadata upload and retrieval."""
        test_bucket = f"test-bucket-{uuid.uuid4().hex[:8]}"
        object_name = f"test-metadata-{uuid.uuid4().hex}.txt"
        test_metadata = {
            "custom-key": "custom-value",
            "author": "integration-test",
        }

        try:
            # Create bucket
            minio_service.ensure_bucket(test_bucket)

            # Upload object with metadata
            minio_service.upload_data(
                object_name=object_name,
                data=b"metadata test content",
                bucket_name=test_bucket,
                metadata=test_metadata,
            )

            # Retrieve object metadata
            stat = minio_service.stat_object(
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
            if minio_service.bucket_exists(test_bucket):
                minio_service.client.remove_object(test_bucket, object_name)
                minio_service.client.remove_bucket(test_bucket)
