import faster_whisper
import stable_whisper

from src.config import settings
from src.types.whisper.type_hints import WhisperModel


def load_model() -> WhisperModel:  # type: ignore
    if settings.whisper.use_faster_whisper:
        return faster_whisper.WhisperModel(
            settings.whisper.model_name_or_path,
            compute_type=settings.whisper.ct2_compute_type,
        )
    else:
        return stable_whisper.load_model(settings.whisper.model_name_or_path)
