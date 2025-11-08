import json

from loguru import logger
from rich.console import Console
from rich.text import Text

console = Console()

# Color mapping for log levels
LEVEL_COLORS = {
    "TRACE": "dim cyan",
    "DEBUG": "cyan",
    "INFO": "green",
    "SUCCESS": "bold green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold red on white",
}


def rich_json_sink(message):
    record = message.record
    level = record["level"].name

    # Build proper JSON structure
    log_data = {
        "time": record["time"].isoformat(),
        "level": level,
        "message": record["message"],
    }

    # Add extra fields if present
    if record["extra"]:
        log_data["extra"] = record["extra"]

    # Add context
    log_data["context"] = {
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "file": record["file"].name,
    }

    # Convert to formatted JSON string
    json_str = json.dumps(log_data, indent=2)

    # Colorize the JSON
    output = Text()
    in_extra = False
    in_context = False

    for line in json_str.split("\n"):
        # Track which section we're in
        if '"extra":' in line:
            in_extra = True
            in_context = False
        elif '"context":' in line:
            in_context = True
            in_extra = False
        elif line.strip() in ["},", "}"]:
            # Check if we're leaving a section
            if in_extra or in_context:
                in_extra = False
                in_context = False

        # Color the keys
        if '": ' in line:
            key_part, value_part = line.split('": ', 1)
            key_part += '": '

            # Determine color based on content
            if '"time"' in key_part:
                output.append(key_part, style="blue")
                output.append(value_part, style="green")
            elif '"level"' in key_part:
                output.append(key_part, style="blue")
                # Color the level value based on severity
                level_color = LEVEL_COLORS.get(level, "white")
                output.append(value_part, style=level_color)
            elif '"message"' in key_part:
                output.append(key_part, style="blue")
                output.append(value_part, style="white")
            elif '"extra"' in key_part or '"context"' in key_part:
                output.append(key_part, style="blue")
                output.append(value_part, style="dim white")
            # Nested keys in extra/context - split key and value coloring
            elif in_extra or in_context:
                # Keys in dim blue, values in yellow
                output.append(key_part, style="dim blue")
                output.append(value_part, style="yellow")
            else:
                output.append(line, style="white")
        else:
            # Braces and brackets
            output.append(line, style="dim white")
        output.append("\n")

    console.print(output, end="")


logger.remove()  # Remove default handler
logger.add(rich_json_sink, format="{message}")

# Test different log levels
logger.trace("trace message", user="brandon", count=1)
logger.debug("debug message", user="brandon", count=2)
logger.info("info message", user="brandon", count=3)
logger.success("success message", user="brandon", count=4)
logger.warning("warning message", user="brandon", count=5)
logger.error("error message", user="brandon", count=6)
logger.critical("critical message", user="brandon", count=7)
