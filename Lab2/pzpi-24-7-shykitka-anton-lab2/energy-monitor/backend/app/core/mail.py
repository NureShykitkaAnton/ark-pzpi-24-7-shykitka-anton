"""Сервіс надсилання електронних повідомлень із безпечним локальним резервом (mock)."""

import logging

from app.core.config import settings

logger = logging.getLogger("energymon.mail")


class MailService:
    """Сервіс сповіщень електронною поштою."""

    async def send_notification_email(
        self, email: str, subject: str, html_body: str
    ) -> None:
        """Логує або надсилає службове повідомлення користувачу."""
        logger.info(
            "[MAIL] To: %s | Subject: %s | Project: %s",
            email,
            subject,
            settings.PROJECT_NAME,
        )
