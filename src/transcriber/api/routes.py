from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, File, UploadFile
from src.transcriber.services.audio import validate_audio_file
from src.transcriber.services.deduplication import (
    calculate_audio_hash,
)
from src.transcriber.services.governance import (
    validate_transcription_request,
)
from src.transcriber.services.guardrails import (
    apply_transcription_guardrails,
)
from src.transcriber.services.transcription import (
    transcription_service,
)

router = APIRouter()


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "").suffix.lower()

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await audio.read())
        temp_path = temp_file.name

    try:
        validate_audio_file(temp_path)
        validate_transcription_request(temp_path)

        result = transcription_service.transcribe(temp_path)

        result["segments"] = [
            {
                **segment,
                "text": apply_transcription_guardrails(segment["text"]),
            }
            for segment in result["segments"]
        ]

        result["text"] = " ".join(
            segment["text"] for segment in result["segments"]
        )

        result["filename"] = audio.filename
        result["audio_hash"] = calculate_audio_hash(temp_path)

        return result

    finally:
        Path(temp_path).unlink(missing_ok=True)