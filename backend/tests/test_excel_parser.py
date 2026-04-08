"""
Tests for app.services.excel_parser — covers all parsing edge cases.
"""

from __future__ import annotations

import io
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.core.exceptions import ExcelParseError, InvalidFileTypeError
from app.services.excel_parser import EmailRecipient, parse_recipients


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_upload(filename: str, data: bytes) -> MagicMock:
    """Create a mock UploadFile with the given filename and data bytes."""
    mock = MagicMock()
    mock.filename = filename
    mock.file = io.BytesIO(data)
    return mock


def _csv_bytes(rows: list[list[str]]) -> bytes:
    """Build CSV bytes from a list of rows (first row = headers)."""
    lines = [",".join(row) for row in rows]
    return "\n".join(lines).encode("utf-8")


def _xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to xlsx bytes in memory."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParseRecipientsValid:
    """Happy-path tests for valid input."""

    def test_valid_xlsx_with_name_and_email(self):
        """Standard xlsx with name + email columns returns correct list."""
        df = pd.DataFrame({
            "Company Name": ["Acme Corp", "Globex Inc"],
            "Email": ["hr@acme.com", "jobs@globex.com"],
        })
        upload = _make_upload("contacts.xlsx", _xlsx_bytes(df))
        recipients, skipped = parse_recipients(upload)

        assert len(recipients) == 2
        assert skipped == 0
        assert recipients[0].name == "Acme Corp"
        assert recipients[0].email == "hr@acme.com"
        assert recipients[1].name == "Globex Inc"
        assert recipients[1].email == "jobs@globex.com"

    def test_csv_input_works(self):
        """CSV files are parsed correctly."""
        data = _csv_bytes([
            ["Name", "E-mail"],
            ["Wayne Enterprises", "apply@wayne.com"],
            ["Stark Industries", "hire@stark.com"],
        ])
        upload = _make_upload("contacts.csv", data)
        recipients, skipped = parse_recipients(upload)

        assert len(recipients) == 2
        assert skipped == 0

    def test_extra_columns_ignored(self):
        """Columns not matching name/email aliases are silently ignored."""
        data = _csv_bytes([
            ["Company", "Email", "Phone", "Country"],
            ["Acme", "hr@acme.com", "555-0100", "US"],
        ])
        upload = _make_upload("data.csv", data)
        recipients, skipped = parse_recipients(upload)

        assert len(recipients) == 1
        assert recipients[0].name == "Acme"
        assert recipients[0].email == "hr@acme.com"


class TestParseRecipientsDedup:
    """Deduplication tests."""

    def test_duplicate_emails_deduplicated(self):
        """Case-insensitive duplicates keep first occurrence only."""
        data = _csv_bytes([
            ["Name", "Email"],
            ["First", "hr@acme.com"],
            ["Second", "HR@ACME.COM"],
            ["Third", "hr@acme.com"],
        ])
        upload = _make_upload("dupes.csv", data)
        recipients, skipped = parse_recipients(upload)

        assert len(recipients) == 1
        assert recipients[0].name == "First"
        assert skipped == 2


class TestParseRecipientsInvalid:
    """Invalid-input edge cases."""

    def test_missing_email_column_raises(self):
        """No recognisable email column → ExcelParseError."""
        data = _csv_bytes([
            ["Company", "Phone"],
            ["Acme", "555-0100"],
        ])
        upload = _make_upload("no_email.csv", data)

        with pytest.raises(ExcelParseError, match="email column"):
            parse_recipients(upload)

    def test_all_emails_invalid_raises(self):
        """100 % invalid emails → ExcelParseError."""
        data = _csv_bytes([
            ["Name", "Email"],
            ["A", "not-an-email"],
            ["B", "also-bad"],
        ])
        upload = _make_upload("bad.csv", data)

        with pytest.raises(ExcelParseError):
            parse_recipients(upload)

    def test_empty_file_raises(self):
        """File with headers only → ExcelParseError."""
        data = _csv_bytes([["Name", "Email"]])
        upload = _make_upload("empty.csv", data)

        with pytest.raises(ExcelParseError, match="empty"):
            parse_recipients(upload)

    def test_unsupported_extension_raises(self):
        """Non .xlsx/.csv extension → InvalidFileTypeError."""
        upload = _make_upload("data.txt", b"some data")

        with pytest.raises(InvalidFileTypeError):
            parse_recipients(upload)


class TestParseRecipientsMixed:
    """Mixed valid / invalid rows."""

    def test_mixed_valid_invalid_below_threshold(self):
        """
        < 50 % invalid → valid rows returned, invalid skipped.
        """
        data = _csv_bytes([
            ["Name", "Email"],
            ["Good1", "a@b.com"],
            ["Good2", "c@d.com"],
            ["Good3", "e@f.com"],
            ["Bad", "not-email"],
        ])
        upload = _make_upload("mixed.csv", data)
        recipients, skipped = parse_recipients(upload)

        assert len(recipients) == 3
        assert skipped == 1
