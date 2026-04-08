"""
Gmail API client — build service, send emails, refresh OAuth credentials.
"""

from __future__ import annotations

import base64
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from google.auth.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from app.config import Settings
from app.core.exceptions import GmailAuthError, GmailQuotaError, GmailSendError
from app.core.security import GOOGLE_SCOPES
from app.db.models import UserToken
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_gmail_service(credentials: Credentials) -> Resource:
    """
    Construct a Gmail API ``Resource`` from the given credentials.

    The ``cache_discovery=False`` argument avoids file-cache permission
    warnings on Windows / serverless environments.
    """
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def send_email(
    service: Resource,
    to: str,
    subject: str,
    body: dict[str, str],
    resume_bytes: bytes,
    resume_filename: str,
) -> dict[str, str]:
    """
    Compose and send one email with a PDF attachment via the Gmail API.

    Parameters
    ----------
    service : Resource
        Authenticated Gmail API resource.
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    body : dict
        ``{"plain": ..., "html": ...}`` as returned by ``build_email_body``.
    resume_bytes : bytes
        Raw PDF bytes of the resume attachment.
    resume_filename : str
        Filename presented to the recipient (e.g. ``resume.pdf``).

    Returns
    -------
    dict
        ``{"message_id": "...", "status": "sent"}``

    Raises
    ------
    GmailQuotaError
        On HTTP 429.
    GmailAuthError
        On HTTP 401 / 403.
    GmailSendError
        On any other Gmail HTTP error.
    """
    # ---- Build MIME message -------------------------------------------------
    msg = MIMEMultipart("mixed")
    msg["To"] = to
    msg["Subject"] = subject

    # Alternative part (plain + HTML)
    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body["plain"], "plain", "utf-8"))
    alt_part.attach(MIMEText(body["html"], "html", "utf-8"))
    msg.attach(alt_part)

    # PDF attachment
    pdf_part = MIMEApplication(resume_bytes, _subtype="pdf")
    pdf_part.add_header(
        "Content-Disposition",
        "attachment",
        filename=resume_filename,
    )
    msg.attach(pdf_part)

    # ---- Encode & send -----------------------------------------------------
    raw_bytes = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    try:
        result: dict[str, Any] = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_bytes})
            .execute()
        )
        message_id = result.get("id", "")
        logger.info("email_sent", to=to, message_id=message_id)
        return {"message_id": message_id, "status": "sent"}

    except HttpError as exc:
        status_code = exc.resp.status if exc.resp else 0
        reason = str(exc)

        if status_code == 429:
            raise GmailQuotaError(
                message="Gmail daily sending quota exceeded.",
                detail={"status": status_code, "reason": reason},
            ) from exc

        if status_code in (401, 403):
            raise GmailAuthError(
                message="Gmail authentication failed. Please re-authenticate.",
                detail={"status": status_code, "reason": reason},
            ) from exc

        raise GmailSendError(
            message=f"Gmail API error ({status_code}).",
            detail={"status": status_code, "reason": reason},
        ) from exc


def refresh_credentials(token: UserToken, settings: Settings) -> OAuth2Credentials:
    """
    Build ``google.oauth2.credentials.Credentials`` from a stored ``UserToken``
    and attempt a token refresh if necessary.

    Raises
    ------
    GmailAuthError
        If the refresh fails (e.g. revoked token, missing refresh_token).
    """
    logger.info(
        "building_credentials",
        user_email=token.user_email,
        has_access_token=bool(token.access_token),
        has_refresh_token=bool(token.refresh_token),
    )

    if not token.refresh_token:
        raise GmailAuthError(
            message="No refresh token stored. Please re-authenticate via /api/v1/auth/login.",
            detail={"user_email": token.user_email},
        )

    creds = OAuth2Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES,
    )

    # Always refresh to ensure we have a fresh, valid token
    try:
        creds.refresh(GoogleRequest())
        logger.info("credentials_refreshed", user_email=token.user_email)
    except Exception as exc:
        logger.error(
            "credentials_refresh_failed",
            user_email=token.user_email,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise GmailAuthError(
            message="Failed to refresh Google credentials. Please re-authenticate.",
            detail={"error": str(exc)},
        ) from exc

    return creds
