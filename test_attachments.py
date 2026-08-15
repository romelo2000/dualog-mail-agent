"""
Автономный тест извлечения и упаковки вложений (без сети, без .env).
Запуск: python test_attachments.py
"""
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from mail_fetcher import Attachment, FetchedMail, _extract_attachments, _extract_body
from mail_forwarder import _build_forward_message

logger = logging.getLogger("test")
logger.addHandler(logging.NullHandler())


def _build_test_message_with_attachment(size_bytes: int, filename: str = "report.pdf") -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = "captain@ship.example"
    msg["Subject"] = "Test survey report"
    msg.attach(MIMEText("Please see attached report.", "plain", "utf-8"))

    part = MIMEApplication(b"x" * size_bytes, _subtype="pdf")
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)
    return msg


def test_extract_small_attachment_included():
    msg = _build_test_message_with_attachment(size_bytes=1024, filename="small.pdf")
    attachments = _extract_attachments(msg, max_size_mb=10, logger=logger, uid="1")
    assert len(attachments) == 1, "Маленькое вложение должно быть извлечено"
    assert attachments[0].filename == "small.pdf"
    assert len(attachments[0].content) == 1024


def test_extract_oversized_attachment_skipped():
    msg = _build_test_message_with_attachment(size_bytes=2 * 1024 * 1024, filename="big.pdf")
    attachments = _extract_attachments(msg, max_size_mb=1, logger=logger, uid="2")
    assert attachments == [], "Вложение больше лимита должно быть пропущено"


def test_body_still_extracted_with_attachment_present():
    msg = _build_test_message_with_attachment(size_bytes=100, filename="x.pdf")
    body = _extract_body(msg)
    assert "Please see attached report" in body


def test_build_forward_message_includes_attachment():
    mail = FetchedMail(
        uid="3",
        sender="captain@ship.example",
        subject="Urgent survey",
        body="body text",
        raw=b"",
        attachments=[Attachment(filename="doc.pdf", content=b"PDFDATA", content_type="application/pdf")],
    )
    msg = _build_forward_message(mail, from_addr="agent@gmail.com", to_addr="me@gmail.com")

    filenames = []
    for part in msg.walk():
        disp = part.get("Content-Disposition") or ""
        if "attachment" in disp:
            filenames.append(part.get_filename())

    assert filenames == ["doc.pdf"], f"Ожидалось вложение doc.pdf в письме, получили: {filenames}"


def test_build_forward_message_without_attachments():
    mail = FetchedMail(
        uid="4", sender="x@x.com", subject="No attach", body="body", raw=b"",
    )
    msg = _build_forward_message(mail, from_addr="agent@gmail.com", to_addr="me@gmail.com")
    for part in msg.walk():
        disp = part.get("Content-Disposition") or ""
        assert "attachment" not in disp


def run_all():
    tests = [
        test_extract_small_attachment_included,
        test_extract_oversized_attachment_skipped,
        test_body_still_extracted_with_attachment_present,
        test_build_forward_message_includes_attachment,
        test_build_forward_message_without_attachments,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {e}")

    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()
