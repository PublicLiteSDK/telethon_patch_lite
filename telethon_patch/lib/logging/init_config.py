import sys
from . import logger

# ANSI для ярко-белого
ANSI_BRIGHT_WHITE = "\033[97m"
ANSI_RESET = "\033[0m"

level_colors = {
    "DEBUG": "dim",
    "SUCCESS": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red on white"
}


def format_record(record):
    level = record["level"].name
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S")
    message = record["message"]

    if level == "INFO":
        return f"<white>[{timestamp}] ||</white> {ANSI_BRIGHT_WHITE}{message}{ANSI_RESET}\n"

    color = level_colors.get(level, "white")
    return f"<white>[{timestamp}] ||</white> <{color}>{message}</{color}>\n"


def init_logging_config(level="INFO", logging_path="logs/main.log"):
    logger.remove()
    logger.add(logging_path, level=level, rotation="1 MB", compression="zip",
               format="[{time:YYYY-MM-DD HH:mm:ss}] || {message}")
    logger.add(sys.stderr, level=level, format=format_record)
