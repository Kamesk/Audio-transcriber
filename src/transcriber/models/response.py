from pydantic import BaseModel, Field


class TranscriptionSegment(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    text: str


class TranscriptionResponse(BaseModel):
    filename: str
    language: str
    language_probability: float
    duration: float
    text: str
    segments: list[TranscriptionSegment]