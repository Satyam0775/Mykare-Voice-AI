"""
Logging configuration — writes structured JSON to logs/app.log and plain text to stdout.
"""
import logging
import sys
from pathlib import Path

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    Path("logs").mkdir(exist_ok=True)

    # Root stdlib logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    fmt = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(fmt))

    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    # structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
