import logging

import av
import numpy as np
import torch
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad, get_speech_timestamps

from src.transcriber.config.settings import settings


logger = logging.getLogger(__name__)


class TranscriptionService:

    SAMPLE_RATE = 16000

    def __init__(self):
        logger.info(
            "Loading Whisper model | model=%s | device=%s | compute_type=%s",
            settings.MODEL_NAME,
            settings.DEVICE,
            settings.COMPUTE_TYPE,
        )

        self.model = WhisperModel(
            settings.MODEL_NAME,
            device=settings.DEVICE,
            compute_type=settings.COMPUTE_TYPE,
        )

        logger.info("Loading Silero VAD model")

        self.vad_model = load_silero_vad()

        logger.info("Whisper + VAD models loaded successfully")


    def _load_audio(self, audio_path: str) -> np.ndarray:

        logger.info(
            "Decoding audio with PyAV | file=%s",
            audio_path,
        )

        container = av.open(audio_path)

        audio_stream = next(
            stream for stream in container.streams
            if stream.type == "audio"
        )

        source_sample_rate = audio_stream.sample_rate

        resampler = av.audio.resampler.AudioResampler(
            format="s16",
            layout="mono",
            rate=self.SAMPLE_RATE,
        )

        audio_frames = []

        for frame in container.decode(audio=0):

            resampled_frames = resampler.resample(frame)

            if not isinstance(resampled_frames, list):
                resampled_frames = [resampled_frames]

            for resampled_frame in resampled_frames:

                frame_array = resampled_frame.to_ndarray()

                audio_frames.append(frame_array)

        remaining_frames = resampler.resample(None)

        if remaining_frames:

            if not isinstance(remaining_frames, list):
                remaining_frames = [remaining_frames]

            for frame in remaining_frames:
                audio_frames.append(frame.to_ndarray())

        container.close()

        if not audio_frames:
            raise ValueError("No audio data found")

        audio = np.concatenate(
            audio_frames,
            axis=1,
        )

        audio = audio.squeeze()

        # int16 -> float32 [-1, 1]
        audio = audio.astype(np.float32) / 32768.0

        logger.info(
            "Audio decoded | source_sample_rate=%s | "
            "target_sample_rate=%s | duration=%.2fs",
            source_sample_rate,
            self.SAMPLE_RATE,
            len(audio) / self.SAMPLE_RATE,
        )

        return audio

    def _detect_speech(self, audio: np.ndarray):

        logger.info("Running Silero VAD")

        audio_tensor = torch.from_numpy(audio)

        speech_regions = get_speech_timestamps(
            audio_tensor,
            self.vad_model,
            sampling_rate=self.SAMPLE_RATE,
            return_seconds=True,
            min_speech_duration_ms=250,
            min_silence_duration_ms=500,
        )

        logger.info(
            "VAD completed | speech_regions=%d",
            len(speech_regions),
        )

        return speech_regions

    def transcribe(self, audio_path: str):

        logger.info(
            "Transcription started | file=%s",
            audio_path,
        )


        audio = self._load_audio(audio_path)

        total_duration = len(audio) / self.SAMPLE_RATE

        logger.info(
            "Audio ready | duration=%.2fs | chunk_size=%ss",
            total_duration,
            settings.CHUNK_DURATION_SECONDS,
        )

        speech_regions = self._detect_speech(audio)

        if not speech_regions:
            raise ValueError("No speech detected in audio")

        all_segments = []

        detected_language = None
        language_probability = 0.0

        chunk_counter = 0

        max_chunk_duration = settings.CHUNK_DURATION_SECONDS

        for region_index, region in enumerate(
            speech_regions,
            start=1,
        ):

            speech_start = region["start"]
            speech_end = region["end"]

            current_start = speech_start

            while current_start < speech_end:

                current_end = min(
                    current_start + max_chunk_duration,
                    speech_end,
                )

                chunk_counter += 1

                start_sample = int(
                    current_start * self.SAMPLE_RATE
                )

                end_sample = int(
                    current_end * self.SAMPLE_RATE
                )

                chunk = audio[
                    start_sample:end_sample
                ]

                chunk_duration = (
                    len(chunk) / self.SAMPLE_RATE
                )

                logger.info(
                    "Processing chunk | "
                    "chunk=%d | region=%d | "
                    "start=%.2fs | end=%.2fs | duration=%.2fs",
                    chunk_counter,
                    region_index,
                    current_start,
                    current_end,
                    chunk_duration,
                )


                transcribe_kwargs = {
                    "beam_size": settings.BEAM_SIZE,
                    "vad_filter": False,
                }

                # Detect language only once.
                if detected_language:
                    transcribe_kwargs["language"] = (
                        detected_language
                    )

                segments, info = self.model.transcribe(
                    chunk,
                    **transcribe_kwargs,
                )

                chunk_segments = list(segments)

                if detected_language is None:

                    detected_language = info.language

                    language_probability = (
                        info.language_probability
                    )

                    logger.info(
                        "Language detected | "
                        "language=%s | probability=%.4f",
                        detected_language,
                        language_probability,
                    )

                for segment in chunk_segments:

                    text = segment.text.strip()

                    if not text:
                        continue

                    absolute_start = (
                        current_start + segment.start
                    )

                    absolute_end = (
                        current_start + segment.end
                    )

                    all_segments.append(
                        {
                            "start": round(
                                absolute_start,
                                3,
                            ),
                            "end": round(
                                absolute_end,
                                3,
                            ),
                            "text": text,
                        }
                    )

                logger.info(
                    "Chunk completed | "
                    "chunk=%d | duration=%.2fs | "
                    "segments=%d",
                    chunk_counter,
                    chunk_duration,
                    len(chunk_segments),
                )

                current_start = current_end


        full_text = " ".join(
            segment["text"]
            for segment in all_segments
        ).strip()

        logger.info(
            "Transcription completed | "
            "duration=%.2fs | chunks=%d | segments=%d",
            total_duration,
            chunk_counter,
            len(all_segments),
        )

        return {
            "language": detected_language,
            "language_probability": language_probability,
            "duration": round(total_duration, 3),
            "chunks_processed": chunk_counter,
            "segments": all_segments,
            "text": full_text,
        }


transcription_service = TranscriptionService()