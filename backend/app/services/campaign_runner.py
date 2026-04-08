"""
Background campaign runner — iterates recipients, sends emails, updates MongoDB.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.core.exceptions import GmailAuthError, GmailQuotaError, GmailSendError
from app.db.models import Campaign, CampaignStatus, EmailLog, EmailStatus, UserToken
from app.services.email_builder import build_email_body
from app.services.gmail_client import build_gmail_service, refresh_credentials, send_email
from app.utils.logger import get_logger
from app.utils.rate_limiter import rate_limit_sleep

logger = get_logger(__name__)


async def run_campaign(
    campaign_id: str,
    resume_bytes: bytes,
    resume_filename: str,
) -> None:
    """
    Core background job that sends emails for every pending recipient in a campaign.

    This function is designed to be called via ``BackgroundTasks.add_task()``.
    It saves documents in batches (every 10 sends) to avoid excessive I/O,
    and handles auth / quota errors by stopping early and marking the campaign
    accordingly.
    """
    settings = get_settings()

    # ---- Load campaign -----------------------------------------------------
    campaign = await Campaign.find_one(Campaign.campaign_id == campaign_id)
    if campaign is None:
        logger.error("campaign_not_found", campaign_id=campaign_id)
        return

    campaign.status = CampaignStatus.RUNNING
    await campaign.save()
    logger.info("campaign_started", campaign_id=campaign_id, total=campaign.total)

    # ---- Load credentials --------------------------------------------------
    user_token = await UserToken.find_one(UserToken.user_email == campaign.user_email)
    if user_token is None:
        campaign.status = CampaignStatus.AUTH_ERROR
        await campaign.save()
        logger.error("user_token_missing", campaign_id=campaign_id)
        return

    try:
        creds = refresh_credentials(user_token, settings)
    except GmailAuthError:
        campaign.status = CampaignStatus.AUTH_ERROR
        await campaign.save()
        logger.error("credentials_refresh_failed", campaign_id=campaign_id)
        return

    # Update stored tokens after potential refresh
    user_token.access_token = creds.token
    if creds.refresh_token:
        user_token.refresh_token = creds.refresh_token
    await user_token.save()

    gmail_service = build_gmail_service(creds)

    # ---- Send loop ---------------------------------------------------------
    pending_logs = await EmailLog.find(
        EmailLog.campaign_id == campaign_id,
        EmailLog.status == EmailStatus.PENDING,
    ).to_list()

    batch_counter = 0
    dirty_logs: list[EmailLog] = []

    for email_log in pending_logs:
        try:
            body = build_email_body(
                recipient_name=email_log.recipient_name,
                description=campaign.description,
            )
            send_email(
                service=gmail_service,
                to=email_log.recipient_email,
                subject=campaign.subject,
                body=body,
                resume_bytes=resume_bytes,
                resume_filename=resume_filename,
            )
            email_log.status = EmailStatus.SENT
            email_log.sent_at = datetime.now(timezone.utc)
            campaign.sent_count += 1
            logger.info(
                "email_delivered",
                campaign_id=campaign_id,
                recipient=email_log.recipient_email,
            )

        except GmailAuthError as exc:
            email_log.status = EmailStatus.FAILED
            email_log.error_detail = exc.message
            campaign.failed_count += 1
            campaign.status = CampaignStatus.AUTH_ERROR
            await email_log.save()
            await campaign.save()
            logger.error(
                "auth_error_stopping",
                campaign_id=campaign_id,
                error=exc.message,
            )
            return

        except GmailQuotaError as exc:
            email_log.status = EmailStatus.FAILED
            email_log.error_detail = exc.message
            campaign.failed_count += 1
            campaign.status = CampaignStatus.QUOTA_EXCEEDED
            await email_log.save()
            await campaign.save()
            logger.error(
                "quota_exceeded_stopping",
                campaign_id=campaign_id,
                error=exc.message,
            )
            return

        except GmailSendError as exc:
            email_log.status = EmailStatus.FAILED
            email_log.error_detail = exc.message
            campaign.failed_count += 1
            logger.warning(
                "send_failed_continuing",
                campaign_id=campaign_id,
                recipient=email_log.recipient_email,
                error=exc.message,
            )

        dirty_logs.append(email_log)
        batch_counter += 1

        # Batch save every 10 sends to reduce DB thrashing
        if batch_counter % 10 == 0:
            for dl in dirty_logs:
                await dl.save()
            await campaign.save()
            dirty_logs.clear()

        # Rate-limit between sends
        await rate_limit_sleep(settings.RATE_LIMIT_DELAY_SECONDS)

    # ---- Save remaining dirty logs -----------------------------------------
    for dl in dirty_logs:
        await dl.save()

    # ---- Finalise ----------------------------------------------------------
    if campaign.failed_count == 0:
        campaign.status = CampaignStatus.COMPLETED
    else:
        campaign.status = CampaignStatus.PARTIAL_FAILURE

    await campaign.save()
    logger.info(
        "campaign_finished",
        campaign_id=campaign_id,
        status=campaign.status.value,
        sent=campaign.sent_count,
        failed=campaign.failed_count,
    )
