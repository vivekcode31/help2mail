"""
Custom exception hierarchy and global FastAPI exception handlers.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Help2MailError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Gmail errors
# ---------------------------------------------------------------------------

class GmailSendError(Help2MailError):
    """Raised when a Gmail API send call fails for a non-auth, non-quota reason."""


class GmailAuthError(Help2MailError):
    """Raised when Gmail returns 401/403 — credentials are invalid or expired."""


class GmailQuotaError(Help2MailError):
    """Raised when Gmail returns 429 — daily sending quota exceeded."""


# ---------------------------------------------------------------------------
# File / parsing errors
# ---------------------------------------------------------------------------

class ExcelParseError(Help2MailError):
    """Raised when the uploaded spreadsheet cannot be parsed correctly."""


class InvalidFileTypeError(Help2MailError):
    """Raised when the uploaded file has an unsupported extension or MIME type."""


class FileTooLargeError(Help2MailError):
    """Raised when the uploaded file exceeds the configured size limit."""


# ---------------------------------------------------------------------------
# Campaign errors
# ---------------------------------------------------------------------------

class NoCampaignRunningError(Help2MailError):
    """Raised when a campaign lookup fails because none is active."""


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

def _build_response(status_code: int, exc: Help2MailError) -> JSONResponse:
    body: dict[str, Any] = {"error": exc.message}
    if exc.detail:
        body["detail"] = exc.detail
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach custom exception handlers to the FastAPI application."""

    @app.exception_handler(GmailAuthError)
    async def _gmail_auth_handler(_req: Request, exc: GmailAuthError) -> JSONResponse:
        return _build_response(401, exc)

    @app.exception_handler(GmailQuotaError)
    async def _gmail_quota_handler(_req: Request, exc: GmailQuotaError) -> JSONResponse:
        return _build_response(429, exc)

    @app.exception_handler(GmailSendError)
    async def _gmail_send_handler(_req: Request, exc: GmailSendError) -> JSONResponse:
        return _build_response(502, exc)

    @app.exception_handler(ExcelParseError)
    async def _excel_parse_handler(_req: Request, exc: ExcelParseError) -> JSONResponse:
        return _build_response(422, exc)

    @app.exception_handler(InvalidFileTypeError)
    async def _invalid_file_handler(
        _req: Request, exc: InvalidFileTypeError
    ) -> JSONResponse:
        return _build_response(415, exc)

    @app.exception_handler(FileTooLargeError)
    async def _file_too_large_handler(
        _req: Request, exc: FileTooLargeError
    ) -> JSONResponse:
        return _build_response(413, exc)

    @app.exception_handler(NoCampaignRunningError)
    async def _no_campaign_handler(
        _req: Request, exc: NoCampaignRunningError
    ) -> JSONResponse:
        return _build_response(404, exc)
