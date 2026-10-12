import re
from src.transcriber.utils.logging import get_logger

logger = get_logger(__name__)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"\b\d{10}\b"
)


def apply_transcription_guardrails(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Transcription returned empty text")

    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)

    logger.info("Transcription guardrails applied")
    return text.strip()