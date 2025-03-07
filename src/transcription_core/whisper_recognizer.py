import warnings
from pathlib import Path
from typing import Any

import faster_whisper
import whisper

from src.config import settings
from src.types.segment_type import SegmentType
from src.types.whisper.type_hints import WhisperModel


class WhisperRecognizer:
    def __init__(self, verbose: bool, progress: Any = None):
        self.verbose = verbose
        self.progress = progress

    def recognize(
        self,
        file_path: str,
        model: WhisperModel,
    ) -> list[SegmentType]:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            if isinstance(model, whisper.Whisper):
                return self._recognize_stable_whisper(
                    file_path, model, settings.whisper
                )
            elif isinstance(model, faster_whisper.WhisperModel) or isinstance(
                model, faster_whisper.BatchedInferencePipeline
            ):
                return self._recognize_faster_whisper(
                    file_path, model, settings.whisper
                )

            else:
                raise ValueError("Unsupported model type")

    def _recognize_stable_whisper(
        self,
        audio_file_path: str,
        model: whisper.Whisper,
    ) -> list[SegmentType]:
        segments = model.transcribe(
            audio=audio_file_path,
            verbose=self.verbose,
            task=settings.whisper.task,
            language=settings.whisper.language,
            beam_size=settings.whisper.beam_size,
        ).segments

        return [
            SegmentType(
                text=segment.text.strip(),
                start=segment.start,
                end=segment.end,
            )
            for segment in segments
        ]

    def _recognize_faster_whisper(
        self,
        audio_file_path: str,
        model: faster_whisper.WhisperModel,
    ) -> list[SegmentType]:
        kwargs = {
            "task": settings.whisper.task,
            "language": settings.whisper.language,
            "beam_size": settings.whisper.beam_size,
            "vad_filter": settings.whisper.vad_filter,
        }
        if settings.whisper.vad_filter:
            kwargs["vad_parameters"] = settings.whisper.vad_parameters

        if settings.whisper.use_batched_transcription:
            kwargs["batch_size"] = settings.whisper.batch_size

        segments, info = model.transcribe(
            audio=audio_file_path,
            **kwargs,
        )

        converted_segments = []
        last_end = 0

        file_name = Path(audio_file_path).name

        file_task = self.progress.add_task(
            f"[bold blue]Transcribing {file_name}",
            total=round(info.duration, 2),
            progress_type="transcribe",
        )

        for segment in segments:
            converted_segments.append(
                SegmentType(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                )
            )

            # Update the progress bar
            progress_update = min(
                segment.end - last_end,
                info.duration - self.progress.tasks[file_task].completed,
            )
            if progress_update > 0:
                self.progress.update(file_task, advance=progress_update)
            last_end = segment.end

        self.progress.update(
            file_task,
            completed=info.duration,
            description=f"[bold green]Transcribing {file_name} Complete 🎉",
        )

        return converted_segments
