"""
Email Delivery Service Module.

Handles outbound email dispatch via local or external SMTP servers.
"""

from email.message import EmailMessage
import logging
import smtplib

logger = logging.getLogger(__name__)


class EmailService:
    """Service class to handle outbound email delivery via local or authenticated external SMTP servers."""

    def __init__(
        self,
        server: str,
        port: int,
        user: str | None,
        password: str | None,
        sender: str,
    ):
        """Initialize the EmailService configuration.

        Args:
            server (str): Hostname or IP address of the SMTP server.
            port (int): Network port for the SMTP server (e.g., 25, 1025, 587).
            user (str | None): Username for authentication (optional).
            password (str | None): Password for authentication (optional).
            sender (str): Default sender email address ('From' header).
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender

    def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = False
    ) -> str:
        """Constructs and delivers an email message.

        Args:
            to_email (str): Recipient's email address.
            subject (str): Email subject line.
            body (str): Message content (plain text or HTML).
            is_html (bool, optional): Set to True if body contains HTML markup.
            Defaults to False.

        Returns:
            str: Status message indicating successful delivery or error details.
        """
        logger.debug(
            "Attempting mail to %s via %s:%s (Auth Pass: %s)",
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
                logger.debug("Connecting to SMTP server %s:%s...", self.server, self.port)
                with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                    logger.debug("Connected! Sending message...")
                    server.send_message(msg)
                    logger.debug("SENT via local mail server!")
                return f"Successfully sent email to '{to_email}' via local mail server."

            # Route 2: External SMTP server with TLS authentication
            logger.debug("Connecting to external SMTP %s:%s...", self.server, self.port)
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                if self.port == 587:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
                logger.debug("SENT via external SMTP!")
            return f"Successfully sent email to '{to_email}' via SMTP."

        except Exception as e:
            logger.error("Failed to send email: %s: %s", type(e).__name__, e, exc_info=True)
            return f"Error sending email: {e}"
