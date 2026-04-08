"""
Beanie ODM document models for campaigns, email logs, and user OAuth tokens.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CampaignStatus(str, enum.Enum):
    """Lifecycle status of a bulk-email campaign."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    AUTH_ERROR = "auth_error"
    QUOTA_EXCEEDED = "quota_exceeded"


class EmailStatus(str, enum.Enum):
    """Delivery status for a single email within a campaign."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------

class Campaign(Document):
    """Represents a single bulk-email campaign submitted by a user."""

    campaign_id: str = Field(default_factory=_generate_uuid)
    user_email: Indexed(str)
    subject: str
    description: str
    status: CampaignStatus = CampaignStatus.PENDING
    total: int = 0
    sent_count: int = 0
    failed_count: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "campaigns"

    def __repr__(self) -> str:
        return f"<Campaign id={self.campaign_id} status={self.status}>"


# ---------------------------------------------------------------------------
# EmailLog
# ---------------------------------------------------------------------------

class EmailLog(Document):
    """Individual send attempt for one recipient in a campaign."""

    log_id: str = Field(default_factory=_generate_uuid)
    campaign_id: Indexed(str)
    recipient_email: str
    recipient_name: str = ""
    status: EmailStatus = EmailStatus.PENDING
    error_detail: Optional[str] = None
    sent_at: Optional[datetime] = None

    class Settings:
        name = "email_logs"

    def __repr__(self) -> str:
        return f"<EmailLog id={self.log_id} to={self.recipient_email} status={self.status}>"


# ---------------------------------------------------------------------------
# UserToken (OAuth credentials)
# ---------------------------------------------------------------------------

class UserToken(Document):
    """Stores Google OAuth2 tokens for a user."""

    token_id: str = Field(default_factory=_generate_uuid)
    user_email: Indexed(str, unique=True)
    access_token: str
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "user_tokens"

    def __repr__(self) -> str:
        return f"<UserToken email={self.user_email}>"
