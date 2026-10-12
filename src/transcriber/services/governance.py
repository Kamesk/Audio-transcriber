from src.transcriber.utils.logging import get_logger
from src.transcriber.config.settings import settings
from src.transcriber.services.audio import validate_audio_file

logger = get_logger(__name__)


def validate_transcription_request(audio_path: str) -> None:
    validate_audio_file(audio_path)

    logger.info(
        "Transcription request accepted | "
        "model=%s | device=%s",
        settings.MODEL_NAME,
        settings.DEVICE,
    )