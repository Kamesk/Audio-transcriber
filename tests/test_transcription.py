from pathlib import Path

import pytest

from src.transcriber.services.audio import validate_audio_file
from src.transcriber.services.deduplication import (
    calculate_audio_hash,
    is_duplicate,
)
from src.transcriber.services.guardrails import (
    apply_transcription_guardrails,
)


def test_validate_audio_file(tmp_path: Path):
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"audio-data")

    validate_audio_file(str(audio_file))


def test_unsupported_audio_format(tmp_path: Path):
    audio_file = tmp_path / "test.txt"
    audio_file.write_bytes(b"audio-data")

    with pytest.raises(ValueError, match="Unsupported audio format"):
        validate_audio_file(str(audio_file))


def test_audio_hash(tmp_path: Path):
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"audio-data")

    audio_hash = calculate_audio_hash(str(audio_file))

    assert len(audio_hash) == 64


def test_duplicate_detection(tmp_path: Path):
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"audio-data")

    processed_hashes = set()

    assert is_duplicate(str(audio_file), processed_hashes) is False
    assert is_duplicate(str(audio_file), processed_hashes) is True


def test_guardrails_redact_email():
    text = "Contact user@example.com for details."

    result = apply_transcription_guardrails(text)

    assert "[REDACTED_EMAIL]" in result
    assert "user@example.com" not in result


def test_guardrails_empty_text():
    with pytest.raises(ValueError, match="empty text"):
        apply_transcription_guardrails("")