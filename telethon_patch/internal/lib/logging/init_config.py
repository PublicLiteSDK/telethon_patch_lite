import sys
from . import logger

_format = "<level>[{time:YYYY-MM-DD HH:mm:ss}] || {message}</level>"


def init_logging_config(level="INFO", logging_path="logs/main.log"):
    logger.remove()
    logger.add(logging_path, level=level, rotation="1 MB", compression="zip", format=_format)
    logger.add(sys.stderr, level=level, format=_format)

    logger.success("Logger initialized")
