"""
Input validators for emails, PDFs, and file sizes.
"""

import re

from app.core.exceptions import FileTooLargeError

# RFC 5322 simplified — covers 99.9 % of real-world addresses
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

_PDF_MAGIC = b"%PDF"


def is_valid_email(email: str) -> bool:
    """Return True if *email* looks like a valid RFC-compliant address."""
    if not email or len(email) > 320:
        return False
    return _EMAIL_RE.match(email.strip()) is not None


def is_valid_pdf(file_bytes: bytes) -> bool:
    """Return True if *file_bytes* starts with the PDF magic bytes."""
    return file_bytes[:4] == _PDF_MAGIC


def check_file_size(size_bytes: int, max_mb: int) -> None:
    """Raise FileTooLargeError if *size_bytes* exceeds *max_mb* megabytes."""
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(
            message=f"File size {size_bytes / (1024 * 1024):.1f} MB exceeds the {max_mb} MB limit.",
            detail={"size_bytes": size_bytes, "max_bytes": max_bytes},
        )
