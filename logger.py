"""Настройка логирования: в файл и в консоль."""
import logging
import sys
from pathlib import Path


def setup_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("dualog_agent")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger  # уже настроен (например, при повторном импорте)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # На Windows консоль по умолчанию может использовать cp1252/cp866, где
    # кириллица вызывает UnicodeEncodeError. Принудительно переключаем на UTF-8,
    # если поток это поддерживает (Python 3.7+, TextIOWrapper).
    # В --noconsole сборке PyInstaller sys.stdout/stderr могут быть None — в этом
    # случае консольный обработчик просто не добавляется (логи всё равно пишутся в файл).
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except Exception:
                pass

    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    return logger
