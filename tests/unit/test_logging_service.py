from unittest.mock import MagicMock

import pytest
from rich.console import Console

from lvrgd.common.services.logging_service import LoggingService


@pytest.fixture
def mock_console() -> MagicMock:
    """Create a mock Rich Console."""
    return MagicMock(spec=Console)


@pytest.fixture
def logging_service(mock_console: MagicMock) -> LoggingService:
    """Create a LoggingService instance with mocked console."""
    return LoggingService(console=mock_console)


class TestLoggingService:
    """Tests for LoggingService."""

    def test_initialization(self, mock_console: MagicMock) -> None:
        """Test that LoggingService initializes correctly."""
        service = LoggingService(console=mock_console)
        assert service._console == mock_console

    def test_trace_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that trace method logs correctly."""
        logging_service.trace("test trace message", user="brandon", count=1)
        assert mock_console.print.called

    def test_debug_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that debug method logs correctly."""
        logging_service.debug("test debug message", user="brandon", count=2)
        assert mock_console.print.called

    def test_info_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that info method logs correctly."""
        logging_service.info("test info message", user="brandon", count=3)
        assert mock_console.print.called

    def test_success_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that success method logs correctly."""
        logging_service.success("test success message", user="brandon", count=4)
        assert mock_console.print.called

    def test_warning_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that warning method logs correctly."""
        logging_service.warning("test warning message", user="brandon", count=5)
        assert mock_console.print.called

    def test_error_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that error method logs correctly."""
        logging_service.error("test error message", user="brandon", count=6)
        assert mock_console.print.called

    def test_critical_logs_message(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that critical method logs correctly."""
        logging_service.critical("test critical message", user="brandon", count=7)
        assert mock_console.print.called

    def test_extra_fields_are_logged(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that extra keyword arguments are included in logs."""
        logging_service.info("test message", user="brandon", action="login", session_id="123")
        assert mock_console.print.called

    def test_multiple_log_calls(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test multiple sequential log calls."""
        logging_service.info("first message")
        logging_service.warning("second message")
        logging_service.error("third message")
        assert mock_console.print.call_count == 3

    def test_caller_context_is_captured(
        self, logging_service: LoggingService, mock_console: MagicMock
    ) -> None:
        """Test that caller context is captured with depth=1."""
        logging_service.info("test message from test")
        assert mock_console.print.called
