"""Email delivery service for price alert notifications."""

import smtplib
from email.message import EmailMessage

from .models import PriceResult


class EmailNotifier:
    """Send threshold-based price alert emails via SMTP over SSL.

    Args:
        None.

    Returns:
        EmailNotifier: Notifier instance configured with SMTP credentials.
    """

    def __init__(self, smtp_address: str, email_address: str, app_password: str) -> None:
        """Initialize SMTP configuration used for outgoing alerts.

        Args:
            smtp_address: SMTP server hostname.
            email_address: Sender email address used for SMTP login.
            app_password: App-specific SMTP password.

        Returns:
            None: This constructor initializes notifier credentials.
        """
        self.smtp_address = smtp_address
        self.email_address = email_address
        self.app_password = app_password

    def send_price_alert(self, to_email: str, product_url: str, price: PriceResult, threshold: float) -> None:
        """Compose and send a price alert email.

        Args:
            to_email: Recipient email address.
            product_url: Product URL included in the alert body.
            price: Parsed current product price.
            threshold: Threshold that triggered the alert.

        Returns:
            None: Sends the email and does not return a value.
        """
        subject = "Plugin Boutique price alert"
        body = (
            f"Price dropped below your threshold.\n"
            f"URL: {product_url}\n"
            f"Current price: {price.formatted}\n"
            f"Threshold: {threshold:.2f}\n"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_address
        msg["To"] = to_email
        msg.set_content(body)

        with smtplib.SMTP_SSL(self.smtp_address, 465) as smtp:
            smtp.login(self.email_address, self.app_password)
            smtp.send_message(msg)
