"""
Structured logging configuration using structlog.

- JSON output in production for machine parsing.
- Pretty coloured console output in development for readability.
- Email addresses are masked in all log events (shows ****@domain.com).
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import structlog

from app.config import get_settings

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})")
_CONFIGURED = False


def _mask_emails(value: Any) -> Any:
    """Recursively mask email local parts in strings, dicts, and lists."""
    if isinstance(value, str):
        return _EMAIL_RE.sub(r"****@\1", value)
    if isinstance(value, dict):
        return {k: _mask_emails(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_mask_emails(v) for v in value)
    return value


def _email_masker(
    _logger: Any,
    _method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """structlog processor that masks email addresses in every field."""
    return _mask_emails(event_dict)


def _configure_once() -> None:
    """Set up structlog processors exactly once."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _email_masker,
    ]

    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure stdlib logging to write to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    # Configure structlog to use stdlib as the backend
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> Any:
    """Return a named structlog logger, initialising config on first call."""
    _configure_once()
    return structlog.get_logger(name)
