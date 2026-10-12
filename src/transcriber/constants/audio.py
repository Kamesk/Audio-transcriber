from enum import Enum


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    MPEG = "mpeg"


SUPPORTED_AUDIO_FORMATS = {
    AudioFormat.WAV.value,
    AudioFormat.MP3.value,
    AudioFormat.MPEG.value,
}

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_DURATION_SECONDS = 600