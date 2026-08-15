"""Пересылка важных писем на Gmail через SMTP с timeout и retry."""
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import Logger

from config import Settings
from mail_fetcher import FetchedMail


def _build_forward_message(mail: FetchedMail, from_addr: str, to_addr: str) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = f"[Dualog forward] {mail.subject}"

    body_text = (
        f"Пересланное важное письмо из Dualog Mail.\n"
        f"Оригинальный отправитель: {mail.sender}\n"
        f"Оригинальная тема: {mail.subject}\n"
        f"\n---\n\n{mail.body}"
    )
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    return msg


def forward_mail(mail: FetchedMail, settings: Settings, logger: Logger) -> bool:
    """
    Отправляет письмо через Gmail SMTP с timeout и retry.
    Возвращает True при успехе, False при controlled fail.
    """
    msg = _build_forward_message(mail, settings.smtp_user, settings.forward_to)

    last_error: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            logger.info(
                f"[SMTP] Пересылка письма UID={mail.uid} '{mail.subject}' на {settings.forward_to} (попытка {attempt})"
            )
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds
            ) as server:
                server.login(settings.smtp_user, settings.smtp_app_password)
                server.sendmail(settings.smtp_user, [settings.forward_to], msg.as_string())
            logger.info(f"[SMTP] Успешно переслано UID={mail.uid}")
            return True
        except Exception as e:
            last_error = e
            logger.error(f"[SMTP] Ошибка (попытка {attempt}/{settings.max_retries}): {e}")
            if attempt < settings.max_retries:
                time.sleep(settings.retry_delay_seconds)

    logger.error(
        f"[SMTP] Все {settings.max_retries} попыток исчерпаны для UID={mail.uid}, статус=failed. Последняя ошибка: {last_error}"
    )
    return False
