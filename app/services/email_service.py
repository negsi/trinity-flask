"""
Email Delivery Service Module.

Handles outbound email dispatch via local or authenticated external SMTP servers.
"""

import logging
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from string import Template
from typing import List, Optional

from markdown_it import MarkdownIt

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
        template_path: Optional[str] = None,
    ) -> None:
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sender = sender

        # Enable raw HTML parsing generically for all HTML blocks & inline tags
        self._md = MarkdownIt("gfm-like", {"html": True})

        # Directly use the injected template path or resolve a clean relative fallback
        if template_path:
            self.template_path = template_path
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.template_path = os.path.join(base_dir, "app", "templates", "base_email.html")

    def _render_template(self, html_content: str) -> str:
        """Injects HTML body content into the external base template."""
        try:
            if self.template_path and os.path.exists(self.template_path):
                with open(self.template_path, "r", encoding="utf-8") as f:
                    template_str = f.read()
                return Template(template_str).safe_substitute(content=html_content)
            else:
                logger.warning("Email template not found at '%s'. Using un-wrapped HTML.", self.template_path)
                return html_content
        except Exception as e:
            logger.error("Error rendering email template: %s", e, exc_info=True)
            return html_content

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: Optional[List[str]] = None,
    ) -> str:
        """
        Constructs and delivers an email message over SMTP with Markdown & Attachment support.
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

            # 1. Plain Text Fallback
            msg.set_content(body)

            # 2. HTML Alternative Rendering
            if not is_html:
                rendered_html = self._md.render(body)
                full_html = self._render_template(rendered_html)
                msg.add_alternative(full_html, subtype="html")
            else:
                msg.add_alternative(self._render_template(body), subtype="html")

            # 3. File Attachments
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        logger.warning("Attachment file not found: %s", file_path)
                        continue

                    ctype, encoding = mimetypes.guess_type(file_path)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"

                    maintype, subtype = ctype.split("/", 1)
                    with open(file_path, "rb") as fp:
                        file_data = fp.read()
                        filename = os.path.basename(file_path)

                        msg.add_attachment(
                            file_data,
                            maintype=maintype,
                            subtype=subtype,
                            filename=filename,
                        )
                    logger.info("Attached file '%s' (%s) to outbound email", filename, ctype)

            # Route 1: Local server or unauthenticated connection
            if self.server in ["localhost", "127.0.0.1"] or not self.password:
                with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                    server.send_message(msg)
                return f"Successfully sent email to '{to_email}' with {len(attachments or [])} attachment(s)."

            # Route 2: External SMTP server with TLS authentication
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                if self.port == 587:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            return f"Successfully sent email to '{to_email}' with {len(attachments or [])} attachment(s)."

        except Exception as e:
            logger.error("Failed to send email to '%s': %s", to_email, e, exc_info=True)
            return f"Error sending email: {e}"
