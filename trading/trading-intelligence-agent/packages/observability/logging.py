"""Structured logging configuration for all services."""
from __future__ import annotations

import logging
import os
import sys

import structlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging(service_name: str = "trading-intel") -> None:
    """Call once at process startup to configure structlog."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    for noisy in ("sqlalchemy.engine", "alembic.runtime.migration", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.get_logger(service_name).info(
        "logging_configured", level=LOG_LEVEL, service=service_name
    )
