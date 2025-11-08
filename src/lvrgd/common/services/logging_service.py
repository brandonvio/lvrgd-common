"""Logging service for structured JSON logging with rich output."""

import json
from typing import Any, ClassVar

from loguru import logger
from rich.console import Console
from rich.text import Text


class LoggingService:
    """Service for structured logging using loguru with rich JSON output.

    Uses depth=1 to ensure caller's context is logged, not this service's context.
    """

    LEVEL_COLORS: ClassVar[dict[str, str]] = {
        "TRACE": "dim cyan",
        "DEBUG": "cyan",
        "INFO": "green",
        "SUCCESS": "bold green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red on white",
    }

    def __init__(self, console: Console) -> None:
        """Initialize the logging service.

        Args:
            console: Rich Console instance for output
        """
        self._console = console
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Configure loguru with rich JSON sink."""
        logger.remove()
        logger.add(self._rich_json_sink, format="{message}", level="TRACE")

    def _rich_json_sink(self, message: Any) -> None:
        """Custom sink that outputs colorized JSON logs.

        Args:
            message: Loguru message object
        """
        record = message.record
        level = record["level"].name

        log_data = {
            "time": record["time"].isoformat(),
            "level": level,
            "message": record["message"],
        }

        if record["extra"]:
            log_data["extra"] = record["extra"]

        log_data["context"] = {
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "file": record["file"].name,
        }

        json_str = json.dumps(log_data, indent=2)
        output = self._colorize_json(json_str, level)
        self._console.print(output, end="")

    def _colorize_json(self, json_str: str, level: str) -> Text:
        """Colorize JSON string with rich formatting.

        Args:
            json_str: JSON string to colorize
            level: Log level for level-specific coloring

        Returns:
            Colorized Text object
        """
        output = Text()
        in_nested = False

        for line in json_str.split("\n"):
            in_nested = self._update_nested_state(line, in_nested=in_nested)

            if '": ' in line:
                self._append_colored_line(output, line, level, in_nested=in_nested)
            else:
                output.append(line, style="dim white")
            output.append("\n")

        return output

    def _update_nested_state(self, line: str, *, in_nested: bool) -> bool:
        """Update whether we're in a nested section.

        Args:
            line: Current line being processed
            in_nested: Current nested state

        Returns:
            Updated nested state
        """
        if '"extra":' in line or '"context":' in line:
            return True
        if line.strip() in ["},", "}"]:
            return False
        return in_nested

    def _append_colored_line(self, output: Text, line: str, level: str, *, in_nested: bool) -> None:
        """Append a colored line to the output.

        Args:
            output: Text object to append to
            line: Line to colorize
            level: Log level
            in_nested: Whether we're in a nested section
        """
        key_part, value_part = line.split('": ', 1)
        key_part += '": '

        if '"time"' in key_part:
            output.append(key_part, style="blue")
            output.append(value_part, style="green")
        elif '"level"' in key_part:
            output.append(key_part, style="blue")
            level_color = self.LEVEL_COLORS.get(level, "white")
            output.append(value_part, style=level_color)
        elif '"message"' in key_part:
            output.append(key_part, style="blue")
            output.append(value_part, style="white")
        elif '"extra"' in key_part or '"context"' in key_part:
            output.append(key_part, style="blue")
            output.append(value_part, style="dim white")
        elif in_nested:
            output.append(key_part, style="dim blue")
            output.append(value_part, style="yellow")
        else:
            output.append(line, style="white")

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
