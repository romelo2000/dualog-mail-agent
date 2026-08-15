"""
Точка входа агента: опрос Dualog IMAP -> фильтр по правилам -> пересылка на Gmail.

Гарантии стабильности:
- каждый IMAP/SMTP вызов имеет timeout и retry (см. mail_fetcher.py / mail_forwarder.py)
- каждый цикл обработки обёрнут watchdog-таймером (CYCLE_WATCHDOG_SECONDS)
- любая ошибка -> controlled fail с логированием, никогда не роняет весь процесс
- нет бесконечных `while True` без выхода из итерации; каждая итерация ограничена по времени
"""
import signal
import threading
import time

from classifier import is_important
from config import BASE_DIR, Rules, Settings
from logger import setup_logger
from mail_fetcher import fetch_new_mails
from mail_forwarder import forward_mail
from state_store import StateStore

_shutdown = threading.Event()


def _handle_signal(signum, frame):
    _shutdown.set()


class WatchdogTimeout(Exception):
    pass


def run_cycle_with_watchdog(settings, logger, state):
    """
    Выполняет один цикл (fetch + classify + forward) в отдельном потоке.
    Если поток не завершился за cycle_watchdog_seconds -> статус failed, логируем timeout,
    основной процесс продолжает жить и переходит к следующему циклу.
    """
    result = {"status": "pending", "error": None}

    def worker():
        try:
            run_single_cycle(settings, logger, state)
            result["status"] = "completed"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=settings.cycle_watchdog_seconds)

    if t.is_alive():
        logger.error(
            f"[WATCHDOG] Цикл превысил лимит {settings.cycle_watchdog_seconds}s -> status=failed, error=timeout"
        )
        # Поток-демон будет убит вместе с процессом позже; здесь просто помечаем как failed
        # и не блокируем основной цикл дальше.
        return "failed"

    if result["status"] == "failed":
        logger.error(f"[CYCLE] status=failed, error={result['error']}")
    else:
        logger.info("[CYCLE] status=completed")

    return result["status"]


def run_single_cycle(settings: Settings, logger, state: StateStore) -> None:
    logger.info("[CYCLE] Старт цикла опроса")

    # Перечитываем rules.yaml перед каждым циклом, чтобы правила можно было
    # редактировать (Блокнотом) без перезапуска агента.
    rules_path = BASE_DIR / "rules.yaml"
    try:
        settings.rules = Rules.load(rules_path)
    except Exception as e:
        logger.error(f"[RULES] Не удалось перечитать rules.yaml, используются старые правила: {e}")

    mails = fetch_new_mails(settings, logger, already_seen=state)

    for mail in mails:
        important = is_important(mail.sender, mail.subject, mail.body, settings.rules)
        if not important:
            logger.info(f"[FILTER] UID={mail.uid} '{mail.subject}' -> не важно, пропуск")
            state.mark_seen(mail.uid)
            continue

        logger.info(f"[FILTER] UID={mail.uid} '{mail.subject}' -> ВАЖНО, пересылка")
        ok = forward_mail(mail, settings, logger)
        if ok:
            state.mark_seen(mail.uid)
        else:
            logger.error(f"[CYCLE] Пересылка не удалась для UID={mail.uid}, попробуем в следующем цикле")

    state.save()
    logger.info("[CYCLE] Цикл завершён")


def main():
    settings = Settings.load()
    logger = setup_logger(settings.log_file)

    # StateStore используется как "already_seen" контейнер с методом __contains__
    state = StateStore(settings.state_file)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("=== Dualog -> Gmail forwarding agent запущен ===")
    logger.info(f"IMAP: {settings.imap_user}@{settings.imap_host}:{settings.imap_port}")
    logger.info(f"Пересылка на: {settings.forward_to}")
    logger.info(f"Интервал опроса: {settings.poll_interval_seconds}s")

    while not _shutdown.is_set():
        cycle_start = time.monotonic()
        try:
            run_cycle_with_watchdog(settings, logger, state)
        except Exception as e:
            # Последний рубеж защиты: даже неожиданная ошибка не должна убить процесс
            logger.error(f"[MAIN] Необработанная ошибка в цикле: {e}")

        elapsed = time.monotonic() - cycle_start
        sleep_for = max(0, settings.poll_interval_seconds - elapsed)
        logger.info(f"[MAIN] Ожидание {sleep_for:.0f}s до следующего цикла")
        _shutdown.wait(timeout=sleep_for)

    logger.info("=== Агент остановлен по сигналу завершения ===")


if __name__ == "__main__":
    main()
