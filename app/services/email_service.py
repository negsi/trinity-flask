from email.message import EmailMessage
import smtplib


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
            str: Status message indicating successful delivery or error
            details.
        """
        print(
            f"[DEBUG] Attempting mail to {to_email} via {self.server}:{self.port} (Auth Pass: {bool(self.password)})"
        )

        try:
            # Create a standard email message object
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = to_email

            # Configure message payload based on content type
            if is_html:
                # Provide a fallback plain-text message for non-HTML mail clients
                msg.set_content("Please enable HTML to view this email.")
                # Attach the HTML content version
                msg.add_alternative(body, subtype="html")
            else:
                msg.set_content(body)

            # Route 1: Local server or unauthenticated connection (e.g., localhost, Mailpit, local Postfix)
            if self.server in ["localhost", "127.0.0.1"] or not self.password:
                print(
                    f"[DEBUG] Connecting to SMTP server {self.server}:{self.port}..."
                )
                with smtplib.SMTP(
                    self.server, self.port, timeout=10
                ) as server:
                    print("[DEBUG] Connected! Sending message...")
                    server.send_message(msg)
                    print("[DEBUG] SENT via local mail server!")
                return (
                    f"Successfully sent email to '{to_email}' via local mail"
                    " server."
                )

            # Route 2: External SMTP server with TLS authentication
            print(
                f"[DEBUG] Connecting to external SMTP {self.server}:{self.port}..."
            )
            with smtplib.SMTP(self.server, self.port, timeout=10) as server:
                # Upgrade connection to secure TLS if using standard submission port 587
                if self.port == 587:
                    server.starttls()
                # Authenticate if credentials are provided
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
                print("[DEBUG] SENT via external SMTP!")
            return f"Successfully sent email to '{to_email}' via SMTP."

        except Exception as e:
            # Catch all transport and configuration errors gracefully
            print(
                f"[DEBUG ERROR] Failed to send email: {type(e).__name__}: {e}"
            )
            return f"Error sending email: {e}"