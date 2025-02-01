from pathlib import Path
from typing import Any

import tqdm

from src.config import settings
from src.export_handlers.exporter import Writer
from src.transcription_core.whisper_recognizer import WhisperRecognizer
from src.types.segment_type import SegmentType
from src.utils import file_utils
from src.utils.whisper import whisper_utils


def prepare_output_directory():
    """Prepare the output directory by creating it if it does not exist."""
    output_dir = Path(settings.output.output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)


def process_local_directory(path, model, progress_info):
    filtered_media_files = file_utils.filter_media_files(
        [path] if path.is_file() else list(path.iterdir())
    )
    files: list[dict[str, Any]] = [
        {"file_name": file.name, "file_path": file} for file in filtered_media_files
    ]

    for idx, file in enumerate(tqdm(files, desc="Local files")):
        new_progress_info = progress_info.copy()
        new_progress_info.update(
            {
                "inner_total": len(files),
                "inner_current": idx + 1,
                "inner_status": "processing",
                "progress": 0.0,
                "remaining_time": None,
            }
        )
        yield new_progress_info, []

        writer = Writer()
        if settings.input.skip_if_output_exist and writer.is_output_exist(
            Path(file["file_name"]).stem, settings.output
        ):
            new_progress_info["inner_status"] = "completed"
            yield new_progress_info, []

            continue

        file_path = str(file["file_path"].absolute())

        recognize_generator = WhisperRecognizer(
            verbose=settings.input.verbose
        ).recognize(
            file_path,
            model,
        )

        while True:
            try:
                new_progress_info.update(next(recognize_generator))
                yield new_progress_info, []
            except StopIteration as exception:
                segments: list[SegmentType] = exception.value
                break

            writer.write_all(Path(file["file_name"]).stem, segments)

            for segment in segments:
                segment["url"] = f"file://{file_path}&t={int(segment['start'])}"
                segment["file_path"] = file_path

            new_progress_info["inner_status"] = "completed"
            new_progress_info["progress"] = 100.0
            yield (
                new_progress_info,
                writer.compact_segments(
                    segments, settings.output.min_words_per_segment
                ),
            )


def main():
    prepare_output_directory()

    model = whisper_utils.load_model()

    for idx, item in enumerate(
        tqdm(settings.urls_or_paths, desc="URLs or local paths")
    ):
        progress_info = {
            "outer_total": len(settings.input.urls_or_paths),
            "outer_current": idx + 1,
            "outer_status": "processing",
        }

        if Path(item).exists():
            print(f"Processing local file: {item}")
            for progress_info in process_local_directory(item, model, progress_info):
                yield progress_info
        else:
            print(f"Processing URL is not supported yet: {item}")
            progress_info["outer_status"] = "skipped"
            yield progress_info
            continue
        progress_info["outer_status"] = "completed"
        yield progress_info
