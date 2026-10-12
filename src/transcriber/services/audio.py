from pathlib import Path
from src.transcriber.utils.logging import get_logger
from src.transcriber.constants.audio import (

    SUPPORTED_AUDIO_FORMATS,
    MAX_FILE_SIZE_BYTES,
)


logger = get_logger(__name__)

def validate_audio_file(audio_path: str) -> None:
    path = Path(audio_path)

    if not path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if not path.is_file():
        logger.error(f"Invalid audio path: {audio_path}")
        raise ValueError(f"Invalid audio path: {audio_path}")

    extension = path.suffix.lower().lstrip(".")

    if extension not in SUPPORTED_AUDIO_FORMATS:
        logger.error(f"Unsupported audio format: .{extension}. Supported formats: {SUPPORTED_AUDIO_FORMATS}")
        raise ValueError(
            f"Unsupported audio format: .{extension}. "
            f"Supported formats: {SUPPORTED_AUDIO_FORMATS}"
        )

    file_size = path.stat().st_size

    if file_size > MAX_FILE_SIZE_BYTES:
        logger.error(f"Audio file exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB")
        raise ValueError(
            f"Audio file exceeds maximum size of "
            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
        )