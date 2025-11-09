"""Test suite for the async MinIO service implementation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from minio.error import S3Error

from lvrgd.common.services.logging_service import LoggingService
from lvrgd.common.services.minio.async_minio_service import (
    ERROR_BUCKET_REQUIRED,
    AsyncMinioService,
)
from lvrgd.common.services.minio.minio_models import MinioConfig


@pytest.fixture
def mock_logger() -> Mock:
    """Return a mock logger for service tests."""
    return Mock(spec=LoggingService)


@pytest.fixture
def valid_config() -> MinioConfig:
    """Provide a baseline MinIO configuration for tests."""
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
) -> tuple[AsyncMinioService, Mock]:
    """Create an AsyncMinioService instance with a mocked client."""
    with patch("lvrgd.common.services.minio.async_minio_service.Minio") as minio_ctor:
        client_instance = Mock()
        minio_ctor.return_value = client_instance
        service = AsyncMinioService(mock_logger, valid_config)
        yield service, client_instance


class TestInitialization:
    """Verify service construction and configuration handling."""

    def test_initializes_client_with_expected_arguments(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Ensure the MinIO client receives the correct parameters."""
        with patch("lvrgd.common.services.minio.async_minio_service.Minio") as minio_ctor:
            client_instance = Mock()
            minio_ctor.return_value = client_instance

            service = AsyncMinioService(mock_logger, valid_config)

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

    def test_init_logs_and_re_raises_on_failure(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Errors during initialization should be logged and propagated."""
        with (
            patch(
                "lvrgd.common.services.minio.async_minio_service.Minio",
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
            AsyncMinioService(mock_logger, valid_config)

        mock_logger.exception.assert_called_once_with(
            "Failed to initialize async MinIO client",
        )


class TestHealthAndBuckets:
    """Exercise health check and bucket utility methods."""

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Health check should return bucket names on success."""
        service, client = service_with_client

        # Mock asyncio.to_thread to return bucket list
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = [
                SimpleNamespace(name="alpha"),
                SimpleNamespace(name="beta"),
            ]

            result = await service.health_check()

            assert result == ["alpha", "beta"]
            mock_to_thread.assert_called_once_with(client.list_buckets)

    @pytest.mark.asyncio
    async def test_health_check_failure_logs_and_raises(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Propagate S3 errors from the health check."""
        service, _client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = S3Error(
                "code",
                "message",
                "resource",
                "request-id",
                "host-id",
                "response",
            )

            with pytest.raises(S3Error):
                await service.health_check()

            service.log.exception.assert_called_once_with("Async MinIO health check failed")

    @pytest.mark.asyncio
    async def test_bucket_exists_delegates_to_client(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """bucket_exists should call the underlying client."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = True

            result = await service.bucket_exists("sample")

            assert result is True
            mock_to_thread.assert_called_once_with(client.bucket_exists, "sample")

    @pytest.mark.asyncio
    async def test_ensure_bucket_skips_when_present(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """ensure_bucket should avoid creating existing buckets."""
        service, _client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = True

            await service.ensure_bucket("existing")

            # Only called once for bucket_exists check
            assert mock_to_thread.call_count == 1

    @pytest.mark.asyncio
    async def test_ensure_bucket_creates_when_missing(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Missing buckets should be created."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            # First call (bucket_exists) returns False, second call (make_bucket) succeeds
            mock_to_thread.side_effect = [False, None]

            await service.ensure_bucket("new-bucket")

            # Called twice: once for bucket_exists, once for make_bucket
            assert mock_to_thread.call_count == 2
            mock_to_thread.assert_any_call(client.bucket_exists, "new-bucket")
            mock_to_thread.assert_any_call(
                client.make_bucket,
                "new-bucket",
                location=service.config.region,
            )

    @pytest.mark.asyncio
    async def test_list_buckets_returns_names(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """list_buckets should return plain bucket names."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = [SimpleNamespace(name="bucket-a")]

            result = await service.list_buckets()

            assert result == ["bucket-a"]
            mock_to_thread.assert_called_once_with(client.list_buckets)


class TestObjectOperations:
    """Validate object-level operations."""

    @pytest.mark.asyncio
    async def test_upload_file_uses_resolved_bucket(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Uploading files should return the object name."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = SimpleNamespace(
                object_name="uploaded.txt",
                etag="etag",
            )

            result = await service.upload_file(
                object_name="uploaded.txt",
                file_path="/tmp/file.txt",
                bucket_name="custom-bucket",
                content_type="text/plain",
            )

            assert result == "uploaded.txt"
            mock_to_thread.assert_called_once_with(
                client.fput_object,
                "custom-bucket",
                "uploaded.txt",
                "/tmp/file.txt",
                content_type="text/plain",
                metadata=None,
            )

    @pytest.mark.asyncio
    async def test_download_file_invokes_client(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Downloading files should call fget_object."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = None

            await service.download_file("object.txt", "/tmp/output.txt")

            mock_to_thread.assert_called_once_with(
                client.fget_object,
                "test-bucket",
                "object.txt",
                "/tmp/output.txt",
            )

    @pytest.mark.asyncio
    async def test_upload_data_returns_object_name(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """Uploading byte payloads should delegate to put_object."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = SimpleNamespace(
                object_name="payload.bin",
                etag="etag",
            )

            result = await service.upload_data("payload.bin", b"hello world")

            assert result == "payload.bin"
            # Verify call was made with correct bucket and object name
            call_args = mock_to_thread.call_args
            assert call_args[0][0] == client.put_object
            assert call_args[0][1] == "test-bucket"
            assert call_args[0][2] == "payload.bin"

    @pytest.mark.asyncio
    async def test_download_data_closes_response(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """download_data should clean up the response object."""
        service, _client = service_with_client

        response = Mock()
        response.read.return_value = b"payload"

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = response

            result = await service.download_data("payload.bin")

            assert result == b"payload"
            response.read.assert_called_once_with()
            response.close.assert_called_once_with()
            response.release_conn.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_list_objects_returns_names(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """list_objects should iterate over returned objects."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = iter(
                [
                    SimpleNamespace(object_name="file-1"),
                    SimpleNamespace(object_name="file-2"),
                ],
            )

            result = await service.list_objects(prefix="", recursive=False)

            assert result == ["file-1", "file-2"]
            mock_to_thread.assert_called_once_with(
                client.list_objects,
                "test-bucket",
                prefix="",
                recursive=False,
            )

    @pytest.mark.asyncio
    async def test_remove_object_invokes_client(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """remove_object should call the client with resolved bucket."""
        service, client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = None

            await service.remove_object("delete-me.txt")

            mock_to_thread.assert_called_once_with(
                client.remove_object,
                "test-bucket",
                "delete-me.txt",
            )

    @pytest.mark.asyncio
    async def test_stat_object_returns_metadata(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """stat_object should return the metadata returned by the client."""
        service, client = service_with_client

        metadata = SimpleNamespace(size=128)

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = metadata

            result = await service.stat_object("file.txt", bucket_name="custom")

            assert result is metadata
            mock_to_thread.assert_called_once_with(
                client.stat_object,
                "custom",
                "file.txt",
            )

    @pytest.mark.asyncio
    async def test_operations_require_bucket_when_no_default(
        self,
        mock_logger: Mock,
        valid_config: MinioConfig,
    ) -> None:
        """Calling object operations without a bucket should raise when no default exists."""
        config = valid_config.model_copy(update={"default_bucket": None})
        with patch("lvrgd.common.services.minio.async_minio_service.Minio") as minio_ctor:
            client_instance = Mock()
            minio_ctor.return_value = client_instance
            service = AsyncMinioService(mock_logger, config)

        with pytest.raises(ValueError, match=ERROR_BUCKET_REQUIRED):
            await service.upload_file("object.txt", "/tmp/file.txt")

    @pytest.mark.asyncio
    async def test_generate_presigned_url(
        self,
        service_with_client: tuple[AsyncMinioService, Mock],
    ) -> None:
        """generate_presigned_url should return the URL from the client."""
        service, _client = service_with_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "https://example.com/presigned"

            result = await service.generate_presigned_url("file.txt")

            assert result == "https://example.com/presigned"
