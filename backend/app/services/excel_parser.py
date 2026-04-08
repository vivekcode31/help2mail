"""
Excel / CSV parser that extracts recipient name + email pairs.
"""

from __future__ import annotations

import io
from difflib import SequenceMatcher
from typing import Any

import pandas as pd
from fastapi import UploadFile
from pydantic import BaseModel

from app.core.exceptions import ExcelParseError, InvalidFileTypeError
from app.utils.logger import get_logger
from app.utils.validators import is_valid_email

logger = get_logger(__name__)

# Fuzzy-match targets for column auto-detection
_EMAIL_ALIASES = ["email", "e-mail", "mail", "email address", "emailaddress"]
_NAME_ALIASES = ["name", "company", "company name", "organization", "org"]

_ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
_FUZZY_THRESHOLD = 0.6


class EmailRecipient(BaseModel):
    """A single validated recipient."""

    name: str
    email: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _best_match(column_name: str, aliases: list[str]) -> float:
    """Return the highest fuzzy-match score of *column_name* against *aliases*."""
    normed = column_name.strip().lower()
    return max(
        SequenceMatcher(None, normed, alias).ratio() for alias in aliases
    )


def _detect_column(
    columns: list[str], aliases: list[str], label: str
) -> str | None:
    """
    Return the column name that best matches the given *aliases*.

    Returns None if no column exceeds the fuzzy threshold.
    """
    best_col: str | None = None
    best_score: float = 0.0

    for col in columns:
        score = _best_match(col, aliases)
        if score > best_score:
            best_score = score
            best_col = col

    if best_score >= _FUZZY_THRESHOLD and best_col is not None:
        logger.info(
            "column_detected",
            label=label,
            column=best_col,
            score=round(best_score, 2),
        )
        return best_col

    return None


def _read_dataframe(file: UploadFile) -> pd.DataFrame:
    """Read an UploadFile into a pandas DataFrame."""
    filename = (file.filename or "").lower()

    if filename.endswith(".csv"):
        raw = file.file.read()
        return pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False)

    if filename.endswith(".xlsx"):
        raw = file.file.read()
        return pd.read_excel(
            io.BytesIO(raw),
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
        )

    raise InvalidFileTypeError(
        message=f"Unsupported file type: '{filename}'. Only .xlsx and .csv are accepted.",
        detail={"filename": filename, "allowed": list(_ALLOWED_EXTENSIONS)},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_recipients(file: UploadFile) -> tuple[list[EmailRecipient], int]:
    """
    Parse an uploaded Excel/CSV file into validated ``EmailRecipient`` objects.

    Returns
    -------
    recipients : list[EmailRecipient]
        Deduplicated, valid recipients.
    skipped : int
        Number of rows skipped due to invalid emails.

    Raises
    ------
    InvalidFileTypeError
        If the file extension is unsupported.
    ExcelParseError
        If the file is empty, has no email column, or too many invalid rows.
    """
    df = _read_dataframe(file)

    if df.empty:
        raise ExcelParseError(message="The uploaded file is empty or contains headers only.")

    columns: list[str] = [str(c) for c in df.columns]

    # --- Detect email column ------------------------------------------------
    email_col = _detect_column(columns, _EMAIL_ALIASES, "email")
    if email_col is None:
        raise ExcelParseError(
            message="Could not find an email column. Expected one of: " + ", ".join(_EMAIL_ALIASES),
            detail={"columns_found": columns},
        )

    # --- Detect name column (optional) --------------------------------------
    name_col = _detect_column(columns, _NAME_ALIASES, "name")

    # --- Iterate rows -------------------------------------------------------
    seen_emails: set[str] = set()
    recipients: list[EmailRecipient] = []
    invalid_rows: list[dict[str, Any]] = []
    skipped = 0

    for idx, row in df.iterrows():
        raw_email = str(row.get(email_col, "")).strip()
        raw_name = str(row.get(name_col, "")).strip() if name_col else ""

        # Skip blank rows
        if not raw_email:
            continue

        # Validate email
        if not is_valid_email(raw_email):
            invalid_rows.append({"row": int(idx) + 2, "value": raw_email})  # +2 for 1-indexed + header
            skipped += 1
            continue

        # Deduplicate (case-insensitive)
        normalised = raw_email.lower()
        if normalised in seen_emails:
            skipped += 1
            continue

        seen_emails.add(normalised)
        recipients.append(EmailRecipient(name=raw_name, email=raw_email))

    total_data_rows = len(invalid_rows) + len(recipients)

    # All rows are invalid
    if total_data_rows == 0:
        raise ExcelParseError(message="The uploaded file is empty or contains headers only.")

    # More than 50 % invalid → reject wholesale
    if total_data_rows > 0 and len(invalid_rows) / total_data_rows > 0.5:
        raise ExcelParseError(
            message=f"{len(invalid_rows)} out of {total_data_rows} rows have invalid emails (>50 %).",
            detail={"invalid_rows": invalid_rows},
        )

    if not recipients:
        raise ExcelParseError(message="No valid email addresses found after validation.")

    if invalid_rows:
        logger.warning(
            "invalid_emails_skipped",
            count=len(invalid_rows),
            rows=invalid_rows[:10],
        )

    logger.info(
        "parse_complete",
        valid=len(recipients),
        skipped=skipped,
    )

    return recipients, skipped
