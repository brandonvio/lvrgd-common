"""Test suite for the simplified MinIO service implementation."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from minio.error import S3Error

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.minio.minio_models import MinioConfig
from lvrgd.common.services.minio.minio_service import ERROR_BUCKET_REQUIRED, MinioService


@pytest.fixture
def mock_logger() -> Mock:
    """Return a mock logger for service tests."""
    return Mock(spec=LoggingService)


@pytest.fixture
def valid_config() -> MinioConfig:
    """Provide a baseline Minio configuration for tests."""
    return MinioConfig(
        endpoint="play.min.io:9000",
        access_key="test-access",
        secret_key="test-secret",
        secure=False,
        region="us-east-1",
        default_bucket="test-bucket",
        auto_create_bucket=False,
    )


@pytest.fixture
def service_with_client(
    mock_logger: Mock,
    valid_config: MinioConfig,
) -> tuple[MinioService, Mock]:
    """Create a MinioService instance with a mocked client."""
    with patch("lvrgd.common.services.minio.minio_service.Minio") as minio_ctor:
        client_instance = Mock()
        minio_ctor.return_value = client_instance
        service = MinioService(mock_logger, valid_config)
        yield service, client_instance


class TestInitialization:
    """Verify service construction and configuration handling."""

    def test_initializes_client_with_expected_arguments(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Ensure the MinIO client receives the correct parameters."""
        with patch("lvrgd.common.services.minio.minio_service.Minio") as minio_ctor:
            client_instance = Mock()
            minio_ctor.return_value = client_instance

            service = MinioService(mock_logger, valid_config)

            minio_ctor.assert_called_once_with(
                valid_config.endpoint,
                access_key=valid_config.access_key,
                secret_key=valid_config.secret_key,
                session_token=valid_config.session_token,
                secure=valid_config.secure,
                region=valid_config.region,
            )
            assert service.config == valid_config
            assert service.log is mock_logger

    def test_auto_creates_bucket_when_configured(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Auto-creation should invoke bucket creation workflow."""
        config = valid_config.model_copy(update={"auto_create_bucket": True})

        with patch("lvrgd.common.services.minio.minio_service.Minio") as minio_ctor:
            client_instance = Mock()
            client_instance.bucket_exists.return_value = False
            minio_ctor.return_value = client_instance

            MinioService(mock_logger, config)

            client_instance.bucket_exists.assert_called_once_with(config.default_bucket)
            client_instance.make_bucket.assert_called_once_with(
                config.default_bucket,
                location=config.region,
            )

    def test_init_logs_and_re_raises_on_failure(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Errors during initialization should be logged and propagated."""
        with (
            patch(
                "lvrgd.common.services.minio.minio_service.Minio",
                side_effect=S3Error(
                    "code",
                    "message",
                    "resource",
                    "request-id",
                    "host-id",
                    "response",
                ),
            ),
            pytest.raises(S3Error),
        ):
            MinioService(mock_logger, valid_config)

        mock_logger.exception.assert_called_once_with(
            "Failed to initialize MinIO client",
        )


class TestHealthAndBuckets:
    """Exercise health check and bucket utility methods."""

    def test_health_check_success(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Health check should return bucket names on success."""
        service, client = service_with_client
        client.list_buckets.return_value = [
            SimpleNamespace(name="alpha"),
            SimpleNamespace(name="beta"),
        ]

        result = service.health_check()

        assert result == ["alpha", "beta"]
        client.list_buckets.assert_called_once_with()

    def test_health_check_failure_logs_and_raises(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Propagate S3 errors from the health check."""
        service, client = service_with_client
        client.list_buckets.side_effect = S3Error(
            "code",
            "message",
            "resource",
            "request-id",
            "host-id",
            "response",
        )

        with pytest.raises(S3Error):
            service.health_check()

        service.log.exception.assert_called_once_with("MinIO health check failed")

    def test_bucket_exists_delegates_to_client(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """bucket_exists should call the underlying client."""
        service, client = service_with_client
        client.bucket_exists.return_value = True

        assert service.bucket_exists("sample") is True
        client.bucket_exists.assert_called_once_with("sample")

    def test_ensure_bucket_skips_when_present(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """ensure_bucket should avoid creating existing buckets."""
        service, client = service_with_client
        client.bucket_exists.return_value = True

        service.ensure_bucket("existing")

        client.bucket_exists.assert_called_once_with("existing")
        client.make_bucket.assert_not_called()

    def test_ensure_bucket_creates_when_missing(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Missing buckets should be created."""
        service, client = service_with_client
        client.bucket_exists.return_value = False

        service.ensure_bucket("new-bucket")

        client.bucket_exists.assert_called_once_with("new-bucket")
        client.make_bucket.assert_called_once_with(
            "new-bucket",
            location=service.config.region,
        )

    def test_list_buckets_returns_names(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """list_buckets should return plain bucket names."""
        service, client = service_with_client
        client.list_buckets.return_value = [SimpleNamespace(name="bucket-a")]

        assert service.list_buckets() == ["bucket-a"]
        client.list_buckets.assert_called_once_with()


class TestObjectOperations:
    """Validate object-level operations."""

    def test_upload_file_uses_resolved_bucket(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Uploading files should return the object name."""
        service, client = service_with_client
        client.fput_object.return_value = SimpleNamespace(
            object_name="uploaded.txt",
            etag="etag",
        )

        result = service.upload_file(
            object_name="uploaded.txt",
            file_path="/tmp/file.txt",
            bucket_name="custom-bucket",
            content_type="text/plain",
        )

        assert result == "uploaded.txt"
        client.fput_object.assert_called_once_with(
            "custom-bucket",
            "uploaded.txt",
            "/tmp/file.txt",
            content_type="text/plain",
            metadata=None,
        )

    def test_download_file_invokes_client(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Downloading files should call fget_object."""
        service, client = service_with_client

        service.download_file("object.txt", "/tmp/output.txt")

        client.fget_object.assert_called_once_with(
            "test-bucket",
            "object.txt",
            "/tmp/output.txt",
        )

    def test_upload_data_returns_object_name(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """Uploading byte payloads should delegate to put_object."""
        service, client = service_with_client
        client.put_object.return_value = SimpleNamespace(
            object_name="payload.bin",
            etag="etag",
        )

        result = service.upload_data("payload.bin", b"hello world")

        assert result == "payload.bin"
        args, kwargs = client.put_object.call_args
        assert args[0] == "test-bucket"
        assert args[1] == "payload.bin"
        assert kwargs["content_type"] is None
        assert kwargs["metadata"] is None

    def test_download_data_closes_response(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """download_data should clean up the response object."""
        service, client = service_with_client
        response = Mock()
        response.read.return_value = b"payload"
        client.get_object.return_value = response

        result = service.download_data("payload.bin")

        assert result == b"payload"
        response.read.assert_called_once_with()
        response.close.assert_called_once_with()
        response.release_conn.assert_called_once_with()

    def test_list_objects_returns_names(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """list_objects should iterate over returned objects."""
        service, client = service_with_client
        client.list_objects.return_value = iter(
            [
                SimpleNamespace(object_name="file-1"),
                SimpleNamespace(object_name="file-2"),
            ],
        )

        assert service.list_objects(prefix="", recursive=False) == ["file-1", "file-2"]
        client.list_objects.assert_called_once_with(
            "test-bucket",
            prefix="",
            recursive=False,
        )

    def test_remove_object_invokes_client(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """remove_object should call the client with resolved bucket."""
        service, client = service_with_client

        service.remove_object("delete-me.txt")

        client.remove_object.assert_called_once_with("test-bucket", "delete-me.txt")

    def test_stat_object_returns_metadata(
        self,
        service_with_client: tuple[MinioService, Mock],
    ) -> None:
        """stat_object should return the metadata returned by the client."""
        service, client = service_with_client
        metadata = SimpleNamespace(size=128)
        client.stat_object.return_value = metadata

        result = service.stat_object("file.txt", bucket_name="custom")

        assert result is metadata
        client.stat_object.assert_called_once_with("custom", "file.txt")

    def test_operations_require_bucket_when_no_default(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Calling object operations without a bucket should raise when no default exists."""
        config = valid_config.model_copy(update={"default_bucket": None})
        with patch("lvrgd.common.services.minio.minio_service.Minio") as minio_ctor:
            client_instance = Mock()
            minio_ctor.return_value = client_instance
            service = MinioService(mock_logger, config)

        with pytest.raises(ValueError, match=ERROR_BUCKET_REQUIRED):
            service.upload_file("object.txt", "/tmp/file.txt")
