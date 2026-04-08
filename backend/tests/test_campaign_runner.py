"""
Tests for app.services.campaign_runner — verify the background send loop.

Uses mongomock-motor for an in-memory MongoDB backend so tests run without
a real MongoDB instance.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.core.exceptions import GmailAuthError, GmailQuotaError, GmailSendError
from app.db.models import (
    Campaign,
    CampaignStatus,
    EmailLog,
    EmailStatus,
    UserToken,
)
from app.services.campaign_runner import run_campaign


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
async def init_mock_db():
    """Initialise Beanie with mongomock-motor for each test."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_db"],
        document_models=[Campaign, EmailLog, UserToken],
    )
    yield
    # Collections are auto-cleaned because mongomock is in-memory


async def _seed(
    n_recipients: int = 2,
    include_token: bool = True,
) -> tuple[Campaign, list[EmailLog], UserToken | None]:
    """Create campaign, email logs, and optionally a user token."""
    campaign = Campaign(
        user_email="user@test.com",
        subject="Test",
        description="Hello",
        status=CampaignStatus.PENDING,
        total=n_recipients,
    )
    await campaign.insert()

    logs = []
    for i in range(n_recipients):
        log = EmailLog(
            campaign_id=campaign.campaign_id,
            recipient_email=f"r{i}@example.com",
            recipient_name=f"Recipient {i}",
            status=EmailStatus.PENDING,
        )
        await log.insert()
        logs.append(log)

    token = None
    if include_token:
        token = UserToken(
            user_email="user@test.com",
            access_token="tok",
            refresh_token="ref",
            token_expiry=datetime.now(timezone.utc),
        )
        await token.insert()

    return campaign, logs, token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunCampaign:
    """Tests for the background campaign runner."""

    @pytest.mark.asyncio
    @patch("app.services.campaign_runner.rate_limit_sleep", new_callable=AsyncMock)
    @patch("app.services.campaign_runner.send_email")
    @patch("app.services.campaign_runner.build_gmail_service")
    @patch("app.services.campaign_runner.refresh_credentials")
    async def test_all_sent_successfully(
        self, mock_refresh, mock_build, mock_send, mock_sleep, init_mock_db
    ):
        """All emails sent → campaign status is COMPLETED."""
        campaign, logs, token = await _seed(2)

        mock_refresh.return_value = MagicMock(token="t", refresh_token="r")
        mock_send.return_value = {"message_id": "m1", "status": "sent"}

        await run_campaign(campaign.campaign_id, b"%PDF-fake", "resume.pdf")

        updated = await Campaign.find_one(Campaign.campaign_id == campaign.campaign_id)
        assert updated.status == CampaignStatus.COMPLETED
        assert updated.sent_count == 2
        assert updated.failed_count == 0

    @pytest.mark.asyncio
    @patch("app.services.campaign_runner.rate_limit_sleep", new_callable=AsyncMock)
    @patch("app.services.campaign_runner.send_email")
    @patch("app.services.campaign_runner.build_gmail_service")
    @patch("app.services.campaign_runner.refresh_credentials")
    async def test_partial_failure(
        self, mock_refresh, mock_build, mock_send, mock_sleep, init_mock_db
    ):
        """One send fails → campaign status is PARTIAL_FAILURE."""
        campaign, logs, token = await _seed(2)

        mock_refresh.return_value = MagicMock(token="t", refresh_token="r")
        mock_send.side_effect = [
            {"message_id": "m1", "status": "sent"},
            GmailSendError("send failed"),
        ]

        await run_campaign(campaign.campaign_id, b"%PDF-fake", "resume.pdf")

        updated = await Campaign.find_one(Campaign.campaign_id == campaign.campaign_id)
        assert updated.status == CampaignStatus.PARTIAL_FAILURE
        assert updated.sent_count == 1
        assert updated.failed_count == 1

    @pytest.mark.asyncio
    @patch("app.services.campaign_runner.rate_limit_sleep", new_callable=AsyncMock)
    @patch("app.services.campaign_runner.send_email")
    @patch("app.services.campaign_runner.build_gmail_service")
    @patch("app.services.campaign_runner.refresh_credentials")
    async def test_auth_error_stops_early(
        self, mock_refresh, mock_build, mock_send, mock_sleep, init_mock_db
    ):
        """GmailAuthError sets campaign status to AUTH_ERROR and stops."""
        campaign, logs, token = await _seed(2)

        mock_refresh.return_value = MagicMock(token="t", refresh_token="r")
        mock_send.side_effect = GmailAuthError("auth failed")

        await run_campaign(campaign.campaign_id, b"%PDF-fake", "resume.pdf")

        updated = await Campaign.find_one(Campaign.campaign_id == campaign.campaign_id)
        assert updated.status == CampaignStatus.AUTH_ERROR

    @pytest.mark.asyncio
    @patch("app.services.campaign_runner.rate_limit_sleep", new_callable=AsyncMock)
    @patch("app.services.campaign_runner.send_email")
    @patch("app.services.campaign_runner.build_gmail_service")
    @patch("app.services.campaign_runner.refresh_credentials")
    async def test_quota_exceeded_stops_early(
        self, mock_refresh, mock_build, mock_send, mock_sleep, init_mock_db
    ):
        """GmailQuotaError sets campaign status to QUOTA_EXCEEDED and stops."""
        campaign, logs, token = await _seed(1)

        mock_refresh.return_value = MagicMock(token="t", refresh_token="r")
        mock_send.side_effect = GmailQuotaError("quota hit")

        await run_campaign(campaign.campaign_id, b"%PDF-fake", "resume.pdf")

        updated = await Campaign.find_one(Campaign.campaign_id == campaign.campaign_id)
        assert updated.status == CampaignStatus.QUOTA_EXCEEDED

    @pytest.mark.asyncio
    async def test_missing_token_sets_auth_error(self, init_mock_db):
        """No UserToken in DB → campaign status is AUTH_ERROR."""
        campaign, logs, _ = await _seed(1, include_token=False)

        await run_campaign(campaign.campaign_id, b"%PDF-fake", "resume.pdf")

        updated = await Campaign.find_one(Campaign.campaign_id == campaign.campaign_id)
        assert updated.status == CampaignStatus.AUTH_ERROR
