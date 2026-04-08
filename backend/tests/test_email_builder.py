"""
Tests for app.services.email_builder — verify plain-text and HTML generation.
"""

from app.services.email_builder import build_email_body


class TestBuildEmailBody:
    """Verify both plain-text and HTML email body generation."""

    def test_with_recipient_name(self):
        """When a recipient name is provided, it appears in the greeting."""
        result = build_email_body("Acme Corp", "I am applying for the SWE role.")

        assert "plain" in result
        assert "html" in result
        assert "Dear Acme Corp" in result["plain"]
        assert "Acme Corp" in result["html"]
        assert "I am applying for the SWE role." in result["plain"]
        assert "I am applying for the SWE role." in result["html"]

    def test_empty_name_fallback(self):
        """Empty recipient name falls back to 'Hiring Team'."""
        result = build_email_body("", "Interested in open positions.")

        assert "Dear Hiring Team" in result["plain"]
        assert "Hiring Team" in result["html"]

    def test_whitespace_name_fallback(self):
        """Whitespace-only name also falls back to 'Hiring Team'."""
        result = build_email_body("   ", "Looking for opportunities.")

        assert "Dear Hiring Team" in result["plain"]

    def test_html_escaping(self):
        """Special characters in name/description are escaped in HTML."""
        result = build_email_body("<script>alert('xss')</script>", "desc & more")

        assert "<script>" not in result["html"]
        assert "&lt;script&gt;" in result["html"]
        assert "desc &amp; more" in result["html"]

    def test_description_verbatim_in_plain(self):
        """The description appears verbatim in the plain-text body."""
        desc = "Multiline\ndescription\nblock"
        result = build_email_body("Test Co", desc)

        assert desc in result["plain"]

    def test_closing_present(self):
        """Both formats include a closing line."""
        result = build_email_body("Co", "desc")

        assert "Best regards" in result["plain"]
        assert "Best regards" in result["html"]
