"""
Email Delivery Service Module.

Handles outbound email dispatch via authenticated or unauthenticated SMTP servers
with Markdown parsing, HTML template wrapping, and file attachments.
"""

from email.message import EmailMessage
import logging
import mimetypes
import os
from pathlib import Path
import smtplib
from string import Template

from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)


class EmailService:
    """Service handling outbound email delivery over SMTP."""

    def __init__(
        self,
        server: str,
        port: int,
        user: str | None,
        password: str | None,
        sender: str,
        template_path: str | Path | None = None,
    ) -> None:
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender
        self._markdown_parser = MarkdownIt("gfm-like", {"html": True})

        if template_path:
            self.template_path = Path(template_path).resolve()
        else:
            base_dir = Path(__file__).resolve().parents[2]
            self.template_path = base_dir / "templates" / "base_email.html"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: list[str | Path] | None = None,
    ) -> str:
        """
        Constructs and delivers an email message over SMTP.

        Args:
            to_email: Target recipient email address.
            subject: Subject line.
            body: Message body (Markdown or raw HTML).
            is_html: If True, treats body as raw HTML without Markdown parsing.
            attachments: List of file paths to attach.

        Returns:
            str: Status description of the email dispatch.
        """
        logger.debug(
            "Sending email to '%s' via %s:%d (auth=%s)",
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

            # 1. Plaintext fallback
            msg.set_content(body)

            # 2. Render HTML alternative
            html_content = body if is_html else self._markdown_parser.render(body)
            wrapped_html = self._render_template(html_content)
            msg.add_alternative(wrapped_html, subtype="html")

            # 3. Attachments
            attached_count = self._attach_files(msg, attachments or [])

            # 4. Dispatch
            self._dispatch_smtp(msg)
            return f"Successfully sent email to '{to_email}' with {attached_count} attachment(s)."
        except Exception as exc:
            logger.error("Failed to send email to '%s': %s", to_email, exc, exc_info=True)
            return f"Error sending email: {exc}"

    def _render_template(self, html_content: str) -> str:
        """Wraps inner HTML body into the configured outer template."""
        if self.template_path and self.template_path.is_file():
            try:
                template_str = self.template_path.read_text(encoding="utf-8")
                return Template(template_str).safe_substitute(content=html_content)
            except OSError as exc:
                logger.warning("Error reading email template at '%s': %s", self.template_path, exc)

        return html_content

    def _attach_files(self, msg: EmailMessage, attachment_paths: list[str | Path]) -> int:
        """Attaches existing local files to the EmailMessage."""
        attached_count = 0
        for file_ref in attachment_paths:
            path = Path(file_ref).resolve()
            if not path.is_file():
                logger.warning("Attachment file not found: %s", path)
                continue

            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"
            maintype, subtype = content_type.split("/", 1)

            try:
                file_bytes = path.read_bytes()
                msg.add_attachment(
                    file_bytes,
                    maintype=maintype,
                    subtype=subtype,
                    filename=path.name,
                )
                attached_count += 1
                logger.info("Attached file '%s' (%s)", path.name, content_type)
            except OSError as exc:
                logger.error("Failed to read attachment '%s': %s", path, exc)

        return attached_count

    def _dispatch_smtp(self, msg: EmailMessage) -> None:
        """Executes the raw SMTP socket transmission."""
        with smtplib.SMTP(self.server, self.port, timeout=15) as server:
            if self.port == 587:
                server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.send_message(msg)
