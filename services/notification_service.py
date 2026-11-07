"""In-app notification access and optional SMTP email delivery."""

from email.message import EmailMessage
import os
import smtplib


class NotificationService:
    def __init__(self, store):
        self.store = store

    def list_for_resident(self, resident_name="", unread_only=False):
        return self.store.list_notifications(resident_name, unread_only)

    def unread_count(self, resident_name=""):
        return len(self.list_for_resident(resident_name, unread_only=True))

    def mark_read(self, notification_id):
        self.store.mark_notification_read(notification_id)

    def mark_all_read(self, resident_name=""):
        self.store.mark_all_notifications_read(resident_name)

    def send_email_if_configured(self, recipient, subject, body):
        if not recipient:
            return False
        try:
            return self.send_email(recipient, subject, body)
        except (OSError, smtplib.SMTPException, ValueError):
            return False

    @staticmethod
    def send_email(recipient, subject, body):
        """Send an email only when SMTP settings are configured; in-app stays available otherwise."""
        host = os.getenv("BMS_SMTP_HOST")
        sender = os.getenv("BMS_SMTP_FROM")
        if not recipient or not host or not sender:
            return False
        message = EmailMessage()
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        port = int(os.getenv("BMS_SMTP_PORT", "587"))
        username = os.getenv("BMS_SMTP_USER", "")
        password = os.getenv("BMS_SMTP_PASSWORD", "")
        use_tls = os.getenv("BMS_SMTP_TLS", "true").lower() != "false"
        with smtplib.SMTP(host, port, timeout=10) as client:
            if use_tls:
                client.starttls()
            if username:
                client.login(username, password)
            client.send_message(message)
        return True
