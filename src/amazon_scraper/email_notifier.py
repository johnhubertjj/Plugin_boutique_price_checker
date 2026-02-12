import smtplib
from email.message import EmailMessage

from .models import PriceResult


class EmailNotifier:
    def __init__(self, smtp_address: str, email_address: str, app_password: str) -> None:
        self.smtp_address = smtp_address
        self.email_address = email_address
        self.app_password = app_password

    def send_price_alert(self, to_email: str, product_url: str, price: PriceResult, threshold: float) -> None:
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
