"""
app/core/email_service.py — SMTP email delivery service for SupplyShield AI.

Sends real HTML emails via SMTP (Gmail, SendGrid, Mailgun, AWS SES, or any custom SMTP server).
If SMTP credentials are not configured in environment, logs the email payload and returns status.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("core.email_service")


class EmailService:
    """Enterprise SMTP email dispatch service."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an HTML email via SMTP.
        Returns True if sent successfully, False otherwise.
        """
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_pass = settings.SMTP_PASSWORD

        sender_email = from_email or settings.SMTP_FROM_EMAIL or smtp_user or "noreply@supplyshield.ai"
        sender_name  = from_name or settings.SMTP_FROM_NAME or "SupplyShield AI"

        if not smtp_host or not smtp_user or not smtp_pass:
            logger.warning(
                f"[email_service] SMTP not configured (SMTP_HOST/USER/PASSWORD missing in .env). "
                f"Email to '{to_email}' with subject '{subject}' was not dispatched via SMTP."
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{sender_name} <{sender_email}>"
            msg["To"]      = to_email

            part_html = MIMEText(html_content, "html", "utf-8")
            msg.attach(part_html)

            logger.info(f"[email_service] Connecting to SMTP server {smtp_host}:{smtp_port}...")
            
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                if settings.SMTP_TLS:
                    server.starttls()

            server.login(smtp_user, smtp_pass)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"[email_service] Email successfully sent to {to_email} ✓")
            return True

        except Exception as e:
            logger.error(f"[email_service] Failed to send email to {to_email}: {e}", exc_info=True)
            return False


email_service = EmailService()
