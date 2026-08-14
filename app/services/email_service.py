"""
Email Delivery Service Module.

Handles outbound email dispatch via local or authenticated external SMTP servers.
"""

from email.message import EmailMessage
import logging
import smtplib
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service handling outbound email delivery over SMTP."""

    def __init__(
        self,
        server: str,
        port: int,
        user: Optional[str],
        password: Optional[str],
        sender: str,
    ) -> None:
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
    ) -> str:
        """
        Constructs and delivers an email message over SMTP.

        Args:
            to_email (str): Recipient email address.
            subject (str): Email subject header.
            body (str): Message content (plain text or HTML).
            is_html (bool): Whether the content should be sent as HTML.

        Returns:
            str: Status description of the delivery outcome.
        """
        logger.debug(
            "Attempting to send email to '%s' via %s:%d (Authenticated: %s)",
            to_email,
            self.server,
            self.port,
            bool(self.password),
        )

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = to_email

            if is_html:
                msg.set_content("Please enable HTML to view this email.")
                msg.add_alternative(body, subtype="html")
            else:
                msg.set_content(body)

            # Route 1: Local server or unauthenticated connection
            if self.server in ["localhost", "127.0.0.1"] or not self.password:
                with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                    server.send_message(msg)
                return f"Successfully sent email to '{to_email}' via local mail server."

            # Route 2: External SMTP server with TLS authentication
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                if self.port == 587:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            return f"Successfully sent email to '{to_email}' via SMTP."

        except Exception as e:
            logger.error("Failed to send email to '%s': %s", to_email, e, exc_info=True)
            return f"Error sending email: {e}"
