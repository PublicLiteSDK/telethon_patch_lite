import sys
from . import logger

_format = "<level>[{time:YYYY-MM-DD HH:mm:ss}] || {message}</level>"

level_colors = {
    "DEBUG": "dim",
    "INFO": "white",
    "SUCCESS": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red on white"
}



def format_record(record):
    level = record["level"].name
    color = level_colors.get(level, "white")
    return f"<{color}>[{record['time']:%Y-%m-%d %H:%M:%S}] || {record['message']}</{color}>\n"


def init_logging_config(level="INFO", logging_path="logs/main.log"):
    logger.remove()
    logger.add(logging_path, level=level, rotation="1 MB", compression="zip",
               format="[{time:YYYY-MM-DD HH:mm:ss}] || {message}")
    logger.add(sys.stderr, level=level, format=format_record)

    logger.success("Logger initialized")
