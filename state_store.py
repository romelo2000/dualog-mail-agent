"""Хранение UID уже обработанных писем, чтобы не пересылать повторно."""
import json
from pathlib import Path


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = self._load()

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, OSError):
            return set()

    def is_seen(self, uid: str) -> bool:
        return uid in self._seen

    def __contains__(self, uid: str) -> bool:
        return uid in self._seen

    def mark_seen(self, uid: str) -> None:
        self._seen.add(uid)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(sorted(self._seen), f)
