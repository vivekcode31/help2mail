"""
Constructs the plain-text and HTML email bodies for a campaign.
"""

from __future__ import annotations

import html as html_mod


def build_email_body(recipient_name: str, description: str) -> dict[str, str]:
    """
    Build personalised plain-text and HTML email bodies.

    Parameters
    ----------
    recipient_name : str
        Company or contact name. Falls back to "Hiring Team" when empty.
    description : str
        The application description provided by the sender — inserted verbatim.

    Returns
    -------
    dict
        ``{"plain": ..., "html": ...}`` ready for MIMEMultipart assembly.
    """
    greeting = recipient_name.strip() if recipient_name.strip() else "Hiring Team"
    escaped_greeting = html_mod.escape(greeting)
    escaped_description = html_mod.escape(description)

    # ---- Plain text --------------------------------------------------------
    plain = (
        f"Dear {greeting},\n"
        f"\n"
        f"{description}\n"
        f"\n"
        f"I have attached my resume for your consideration. "
        f"I look forward to hearing from you.\n"
        f"\n"
        f"Best regards"
    )

    # ---- HTML --------------------------------------------------------------
    html = (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head><meta charset=\"UTF-8\"></head>"
        "<body style=\"font-family: Arial, Helvetica, sans-serif; "
        "font-size: 14px; line-height: 1.6; color: #333;\">"
        f"<p>Dear {escaped_greeting},</p>"
        f"<p>{escaped_description}</p>"
        "<p>I have attached my resume for your consideration. "
        "I look forward to hearing from you.</p>"
        "<p>Best regards</p>"
        "</body></html>"
    )

    return {"plain": plain, "html": html}
