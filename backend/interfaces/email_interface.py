"""
Email interface for Clew Directive — STUB (Coming Soon).

MVP: Raises NotImplementedError. UI shows "Coming Soon" modal.
Future: Amazon SES sends Command Briefing PDF to user's email.

Contract:
    send_briefing(email, pdf_bytes, subject) → bool
"""

from abc import ABC, abstractmethod


class EmailInterface(ABC):
    """Abstract email delivery contract."""

    @abstractmethod
    def send_briefing(self, email: str, pdf_bytes: bytes, subject: str = "") -> bool:
        """
        Send a Command Briefing PDF to the specified email.

        Args:
            email: Recipient email address (used only for this send, never stored).
            pdf_bytes: The generated PDF as bytes.
            subject: Email subject line.

        Returns:
            True if sent successfully, False otherwise.
        """
        ...


class EmailStub(EmailInterface):
    """
    MVP stub: Email delivery is not yet implemented.

    When a user clicks "Email this briefing" on the UI, the frontend
    shows a "Coming Soon" modal. This stub exists so the backend
    interface contract is defined and ready for SES integration.

    Future implementation: Amazon SES
    - HTML version of briefing already exists (pre-WeasyPrint render)
    - Attach PDF as email attachment
    - Email used for single send only, never stored (stateless)
    """

    def send_briefing(self, email: str, pdf_bytes: bytes, subject: str = "") -> bool:
        raise NotImplementedError(
            "Email delivery is not yet implemented. "
            "Future: integrate with Amazon SES. "
            "The HTML briefing template is ready in backend/templates/command_briefing.html. "
            "See docs: https://docs.aws.amazon.com/ses/latest/dg/send-email-api.html"
        )


def create_email_service() -> EmailInterface:
    """Factory: returns the active email implementation."""
    return EmailStub()
