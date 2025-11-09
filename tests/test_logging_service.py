"""Tests for the simplified LoggingService."""

from unittest.mock import patch

import pytest

from lvrgd.common.services import LoggingService


@pytest.fixture
def logging_service() -> LoggingService:
    """Create a LoggingService instance."""
    return LoggingService()


class TestLoggingService:
    """Tests for LoggingService."""

    def test_initialization(self) -> None:
        """Test that LoggingService initializes correctly."""
        service = LoggingService()
        assert service is not None

    def test_trace_logs_message(self, logging_service: LoggingService) -> None:
        """Test that trace method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.trace("test trace message", user="brandon", count=1)
            mock_logger.assert_called_once_with(depth=1)

    def test_debug_logs_message(self, logging_service: LoggingService) -> None:
        """Test that debug method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.debug("test debug message", user="brandon", count=2)
            mock_logger.assert_called_once_with(depth=1)

    def test_info_logs_message(self, logging_service: LoggingService) -> None:
        """Test that info method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.info("test info message", user="brandon", count=3)
            mock_logger.assert_called_once_with(depth=1)

    def test_success_logs_message(self, logging_service: LoggingService) -> None:
        """Test that success method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.success("test success message", user="brandon", count=4)
            mock_logger.assert_called_once_with(depth=1)

    def test_warning_logs_message(self, logging_service: LoggingService) -> None:
        """Test that warning method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.warning("test warning message", user="brandon", count=5)
            mock_logger.assert_called_once_with(depth=1)

    def test_error_logs_message(self, logging_service: LoggingService) -> None:
        """Test that error method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.error("test error message", user="brandon", count=6)
            mock_logger.assert_called_once_with(depth=1)

    def test_critical_logs_message(self, logging_service: LoggingService) -> None:
        """Test that critical method logs correctly."""
        with patch("loguru.logger.opt") as mock_logger:
            logging_service.critical("test critical message", user="brandon", count=7)
            mock_logger.assert_called_once_with(depth=1)

    def test_exception_logs_with_traceback(self, logging_service: LoggingService) -> None:
        """Test that exception method captures exception details."""

        def raise_error() -> None:
            msg = "test error"
            raise ValueError(msg)

        with patch("loguru.logger.opt") as mock_logger:
            try:
                raise_error()
            except ValueError:
                logging_service.exception("test exception message", error_type="ValueError")
            mock_logger.assert_called_once_with(depth=1, exception=True)
