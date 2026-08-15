"""Загрузка конфигурации из .env и rules.yaml."""
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    # Собранный PyInstaller .exe: .env/rules.yaml лежат рядом с exe, а не внутри
    # временной папки распаковки (sys._MEIPASS).
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Отсутствует обязательная переменная окружения: {name}")
    return val


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val else default


@dataclass
class Rules:
    senders: list[str] = field(default_factory=list)
    subject_keywords: list[str] = field(default_factory=list)
    body_keywords: list[str] = field(default_factory=list)
    exclude_senders: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "Rules":
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            senders=[s.lower() for s in data.get("senders", [])],
            subject_keywords=[s.lower() for s in data.get("subject_keywords", [])],
            body_keywords=[s.lower() for s in data.get("body_keywords", [])],
            exclude_senders=[s.lower() for s in data.get("exclude_senders", [])],
        )


@dataclass
class Settings:
    # Dualog IMAP
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str
    imap_folder: str
    imap_use_ssl: bool

    # Gmail SMTP
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_app_password: str
    forward_to: str

    # Поведение
    poll_interval_seconds: int
    imap_timeout_seconds: int
    smtp_timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    cycle_watchdog_seconds: int
    state_file: Path
    log_file: Path
    max_attachment_size_mb: int

    rules: Rules

    @classmethod
    def load(cls) -> "Settings":
        rules_path = BASE_DIR / "rules.yaml"
        return cls(
            imap_host=_env("DUALOG_IMAP_HOST", required=True),
            imap_port=_env_int("DUALOG_IMAP_PORT", 993),
            imap_user=_env("DUALOG_IMAP_USER", required=True),
            imap_password=_env("DUALOG_IMAP_PASSWORD", required=True),
            imap_folder=_env("DUALOG_IMAP_FOLDER", "INBOX"),
            imap_use_ssl=_env_bool("DUALOG_IMAP_USE_SSL", True),
            smtp_host=_env("GMAIL_SMTP_HOST", "smtp.gmail.com"),
            smtp_port=_env_int("GMAIL_SMTP_PORT", 465),
            smtp_user=_env("GMAIL_SMTP_USER", required=True),
            smtp_app_password=_env("GMAIL_SMTP_APP_PASSWORD", required=True),
            forward_to=_env("GMAIL_FORWARD_TO", required=True),
            poll_interval_seconds=_env_int("POLL_INTERVAL_SECONDS", 300),
            imap_timeout_seconds=_env_int("IMAP_TIMEOUT_SECONDS", 25),
            smtp_timeout_seconds=_env_int("SMTP_TIMEOUT_SECONDS", 60),
            max_retries=_env_int("MAX_RETRIES", 3),
            retry_delay_seconds=_env_int("RETRY_DELAY_SECONDS", 2),
            cycle_watchdog_seconds=_env_int("CYCLE_WATCHDOG_SECONDS", 120),
            state_file=BASE_DIR / _env("STATE_FILE", "state/seen_uids.json"),
            log_file=BASE_DIR / _env("LOG_FILE", "logs/agent.log"),
            max_attachment_size_mb=_env_int("MAX_ATTACHMENT_SIZE_MB", 10),
            rules=Rules.load(rules_path),
        )
