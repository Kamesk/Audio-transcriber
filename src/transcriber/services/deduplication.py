import hashlib
from src.transcriber.utils.logging import get_logger
from pathlib import Path

logger = get_logger(__name__)

def calculate_audio_hash(audio_path: str) -> str:
    sha256 = hashlib.sha256()

    with Path(audio_path).open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def is_duplicate(audio_path: str, processed_hashes: set[str]) -> bool:
    audio_hash = calculate_audio_hash(audio_path)

    if audio_hash in processed_hashes:
        return True

    processed_hashes.add(audio_hash)
    return False