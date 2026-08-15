"""IMAP-клиент для Dualog с timeout и retry. Никаких бесконечных ожиданий."""
import email
import imaplib
import socket
import time
from dataclasses import dataclass
from email.header import decode_header
from logging import Logger

from config import Settings


@dataclass
class FetchedMail:
    uid: str
    sender: str
    subject: str
    body: str
    raw: bytes


def _decode(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            out.append(text.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
        return ""
    try:
        return msg.get_payload(decode=True).decode(
            msg.get_content_charset() or "utf-8", errors="replace"
        )
    except Exception:
        return ""


def fetch_new_mails(settings: Settings, logger: Logger, already_seen) -> list[FetchedMail]:
    """
    Подключается к Dualog IMAP с timeout, забирает письма из INBOX,
    которых нет в already_seen. При ошибке — retry до max_retries, затем controlled fail.
    """
    socket.setdefaulttimeout(settings.imap_timeout_seconds)

    last_error: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            logger.info(f"[IMAP] Подключение к {settings.imap_host}:{settings.imap_port} (попытка {attempt})")
            if settings.imap_use_ssl:
                conn = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
            else:
                conn = imaplib.IMAP4(settings.imap_host, settings.imap_port)

            try:
                conn.login(settings.imap_user, settings.imap_password)
                conn.select(settings.imap_folder)

                status, data = conn.uid("search", None, "ALL")
                if status != "OK":
                    raise RuntimeError(f"IMAP search вернул статус {status}")

                uids = data[0].split()
                results: list[FetchedMail] = []

                for uid_bytes in uids:
                    uid = uid_bytes.decode()
                    if uid in already_seen:
                        continue

                    status, msg_data = conn.uid("fetch", uid_bytes, "(RFC822)")
                    if status != "OK" or not msg_data or msg_data[0] is None:
                        logger.error(f"[IMAP] Не удалось получить письмо UID={uid}")
                        continue

                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    sender = _decode(msg.get("From"))
                    subject = _decode(msg.get("Subject"))
                    body = _extract_body(msg)

                    results.append(FetchedMail(uid=uid, sender=sender, subject=subject, body=body, raw=raw))

                logger.info(f"[IMAP] Найдено новых писем: {len(results)}")
                return results
            finally:
                try:
                    conn.logout()
                except Exception:
                    pass

        except Exception as e:
            last_error = e
            logger.error(f"[IMAP] Ошибка (попытка {attempt}/{settings.max_retries}): {e}")
            if attempt < settings.max_retries:
                time.sleep(settings.retry_delay_seconds)

    logger.error(f"[IMAP] Все {settings.max_retries} попыток исчерпаны, статус=failed. Последняя ошибка: {last_error}")
    return []
