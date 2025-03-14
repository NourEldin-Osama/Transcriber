import faster_whisper
import stable_whisper

from Transcriber.config import settings
from Transcriber.types.whisper.type_hints import WhisperModel


def load_model() -> WhisperModel:  # type: ignore
    if (
        settings.whisper.use_faster_whisper
        and settings.whisper.use_batched_transcription
    ):
        model = faster_whisper.WhisperModel(
            settings.whisper.model_name_or_path,
            compute_type=settings.whisper.ct2_compute_type,
        )
        return faster_whisper.BatchedInferencePipeline(model=model)
    elif settings.whisper.use_faster_whisper:
        return faster_whisper.WhisperModel(
            settings.whisper.model_name_or_path,
            compute_type=settings.whisper.ct2_compute_type,
        )
    else:
        return stable_whisper.load_model(settings.whisper.model_name_or_path)
