"""Simplified logging service using colored loguru output."""

import sys
from typing import Any

from loguru import logger


class LoggingService:
    """Service for simple colored logging using loguru.

    Uses depth=1 to ensure caller's context is logged, not this service's context.
    """

    def __init__(self) -> None:
        """Initialize the logging service with default loguru configuration."""
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Configure loguru with colored output."""
        logger.remove()
        logger.add(
            sink=sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
            level="TRACE",
        )

    def trace(self, message: str, **kwargs: Any) -> None:
        """Log a trace message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).trace(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).info(message, **kwargs)

    def success(self, message: str, **kwargs: Any) -> None:
        """Log a success message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).success(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1).critical(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log an exception message with full traceback details.

        Captures the current exception and logs it with complete traceback information.
        Should be called from within an exception handler.

        Args:
            message: Log message
            **kwargs: Additional context fields
        """
        logger.opt(depth=1, exception=True).error(message, **kwargs)
