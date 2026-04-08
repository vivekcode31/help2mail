"""
Status & history routes — check campaign progress, view logs, export CSV.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.db.models import Campaign, EmailLog, EmailStatus, UserToken
from app.utils.logger import get_logger

router = APIRouter(prefix="/campaign", tags=["campaign"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _campaign_summary(campaign: Campaign) -> dict[str, Any]:
    """Build a summary dict for a campaign including live counts."""
    pending = await EmailLog.find(
        EmailLog.campaign_id == campaign.campaign_id,
        EmailLog.status == EmailStatus.PENDING,
    ).count()

    return {
        "campaign_id": campaign.campaign_id,
        "user_email": campaign.user_email,
        "subject": campaign.subject,
        "status": campaign.status.value if campaign.status else None,
        "total": campaign.total,
        "sent": campaign.sent_count,
        "failed": campaign.failed_count,
        "pending": pending,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "updated_at": campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


async def _get_campaign_or_404(campaign_id: str, user_email: str) -> Campaign:
    """Fetch a campaign by ID and verify ownership, or raise 404."""
    campaign = await Campaign.find_one(Campaign.campaign_id == campaign_id)
    if campaign is None or campaign.user_email != user_email:
        raise HTTPException(status_code=404, detail="Campaign not found.")
    return campaign


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/history")
async def campaign_history(
    user_token: UserToken = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List all campaigns for the current user, newest first."""
    campaigns = await Campaign.find(
        Campaign.user_email == user_token.user_email,
    ).sort("-created_at").to_list()

    return [await _campaign_summary(c) for c in campaigns]


@router.get("/{campaign_id}")
async def campaign_status(
    campaign_id: str,
    user_token: UserToken = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the current status and progress counters for a campaign."""
    campaign = await _get_campaign_or_404(campaign_id, user_token.user_email)
    return await _campaign_summary(campaign)


@router.get("/{campaign_id}/logs")
async def campaign_logs(
    campaign_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_token: UserToken = Depends(get_current_user),
) -> dict[str, Any]:
    """Return paginated email-log documents for a campaign."""
    await _get_campaign_or_404(campaign_id, user_token.user_email)

    offset = (page - 1) * page_size
    total = await EmailLog.find(EmailLog.campaign_id == campaign_id).count()

    logs = await (
        EmailLog.find(EmailLog.campaign_id == campaign_id)
        .sort("-sent_at")
        .skip(offset)
        .limit(page_size)
        .to_list()
    )

    return {
        "campaign_id": campaign_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "logs": [
            {
                "id": log.log_id,
                "recipient_name": log.recipient_name,
                "recipient_email": log.recipient_email,
                "status": log.status.value if log.status else None,
                "error_detail": log.error_detail,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            }
            for log in logs
        ],
    }


@router.get("/{campaign_id}/export")
async def campaign_export(
    campaign_id: str,
    user_token: UserToken = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a CSV export of all email-log documents for a campaign."""
    await _get_campaign_or_404(campaign_id, user_token.user_email)

    logs = await (
        EmailLog.find(EmailLog.campaign_id == campaign_id)
        .sort("-sent_at")
        .to_list()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["recipient_name", "recipient_email", "status", "error_detail", "sent_at"])

    for log in logs:
        writer.writerow([
            log.recipient_name,
            log.recipient_email,
            log.status.value if log.status else "",
            log.error_detail or "",
            log.sent_at.isoformat() if log.sent_at else "",
        ])

    buffer.seek(0)
    filename = f"campaign_{campaign_id}_logs.csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
