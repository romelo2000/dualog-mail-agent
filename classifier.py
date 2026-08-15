"""Определение важности письма по простым правилам (без LLM)."""
from config import Rules


def is_important(sender: str, subject: str, body: str, rules: Rules) -> bool:
    sender_l = (sender or "").lower()
    subject_l = (subject or "").lower()
    body_l = (body or "").lower()

    # Исключения имеют приоритет
    for excl in rules.exclude_senders:
        if excl in sender_l:
            return False

    for s in rules.senders:
        if s in sender_l:
            return True

    for kw in rules.subject_keywords:
        if kw in subject_l:
            return True

    for kw in rules.body_keywords:
        if kw in body_l:
            return True

    return False
