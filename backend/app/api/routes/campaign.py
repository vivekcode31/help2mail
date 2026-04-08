"""
Campaign routes — start a new bulk-email campaign.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, Form

from app.api.deps import get_current_user
from app.config import get_settings, Settings
from app.core.exceptions import InvalidFileTypeError
from app.db.models import Campaign, CampaignStatus, EmailLog, EmailStatus, UserToken
from app.services.campaign_runner import run_campaign
from app.services.excel_parser import parse_recipients
from app.utils.logger import get_logger
from app.utils.validators import check_file_size, is_valid_pdf

router = APIRouter(prefix="/campaign", tags=["campaign"])
logger = get_logger(__name__)


@router.post("/start")
async def start_campaign(
    background_tasks: BackgroundTasks,
    excel_file: UploadFile,
    resume: UploadFile,
    subject: str = Form(..., max_length=200),
    description: str = Form(..., max_length=2000),
    user_token: UserToken = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Start a new bulk-email campaign.

    Accepts an Excel/CSV recipient list, a PDF resume, a subject line,
    and an application description. Parses the file, creates a ``Campaign``
    document with one ``EmailLog`` document per recipient, and enqueues the
    background send job.
    """
    user_email = user_token.user_email

    # ---- Duplicate guard ---------------------------------------------------
    running = await Campaign.find_one(
        Campaign.user_email == user_email,
        Campaign.status == CampaignStatus.RUNNING,
    )
    if running:
        raise HTTPException(
            status_code=409,
            detail="A campaign is already running. Wait for it to finish.",
        )

    # ---- Validate resume ---------------------------------------------------
    resume_bytes = await resume.read()
    check_file_size(len(resume_bytes), settings.MAX_RESUME_SIZE_MB)

    if not is_valid_pdf(resume_bytes):
        raise InvalidFileTypeError(
            message="Resume must be a valid PDF file.",
            detail={"filename": resume.filename},
        )

    resume_filename = resume.filename or "resume.pdf"

    # ---- Parse recipients --------------------------------------------------
    recipients, skipped = parse_recipients(excel_file)

    # ---- Create campaign + email logs --------------------------------------
    campaign = Campaign(
        user_email=user_email,
        subject=subject,
        description=description,
        status=CampaignStatus.PENDING,
        total=len(recipients),
    )
    await campaign.insert()

    email_logs = [
        EmailLog(
            campaign_id=campaign.campaign_id,
            recipient_email=r.email,
            recipient_name=r.name,
            status=EmailStatus.PENDING,
        )
        for r in recipients
    ]
    if email_logs:
        await EmailLog.insert_many(email_logs)

    logger.info(
        "campaign_created",
        campaign_id=campaign.campaign_id,
        total=len(recipients),
        skipped=skipped,
    )

    # ---- Enqueue background job --------------------------------------------
    background_tasks.add_task(
        run_campaign,
        campaign_id=campaign.campaign_id,
        resume_bytes=resume_bytes,
        resume_filename=resume_filename,
    )

    return {
        "campaign_id": campaign.campaign_id,
        "total_recipients": len(recipients),
        "skipped_invalid": skipped,
    }
