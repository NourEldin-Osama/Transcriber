from pathlib import Path
from typing import Any


from src.utils.progress import MultipleProgress

from src.config import settings
from src.export_handlers.exporter import Writer
from src.transcription_core.whisper_recognizer import WhisperRecognizer
from src.utils import file_utils
from src.utils.whisper import whisper_utils


def prepare_output_directory():
    """Prepare the output directory by creating it if it does not exist."""
    output_dir = Path(settings.output.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def process_local_directory(path, model):
    filtered_media_files = file_utils.filter_media_files(
        [path] if path.is_file() else list(path.iterdir())
    )
    files: list[dict[str, Any]] = [
        {"file_name": file.name, "file_path": file} for file in filtered_media_files
    ]

    with MultipleProgress() as progress:
        total_files = len(files)
        if total_files == 0:
            print(f"No media files found in {path}.")
            return

        total_task = progress.add_task(
            f"[bold blue]Transcribing {total_files} files",
            total=total_files,
            progress_type="total",
        )

        for file in files:
            writer = Writer()
            file_name = Path(file["file_name"]).stem
            if settings.input.skip_if_output_exist and writer.is_output_exist(
                file_name
            ):
                progress.advance(total_task)
                continue

            file_path = str(file["file_path"].absolute())

            recognizer = WhisperRecognizer(
                verbose=settings.input.verbose, progress=progress
            )
            segments = recognizer.recognize(
                file_path,
                model,
            )

            if not segments:
                print(f"No segments returned for file: {file['file_name']}")
            else:
                writer.write_all(file_name, segments)

            progress.advance(total_task)

        progress.update(
            total_task,
            description="[green]Transcription Complete 🎉",
        )


def transcribe():
    prepare_output_directory()
    model = whisper_utils.load_model()

    for item in settings.input.urls_or_paths:
        if Path(item).exists():
            # Handle local file or directory input
            process_local_directory(Path(item), model)

        elif item.startswith("http") or item.startswith("www"):
            # Handle URL input
            print(f"Processing URL: {item}")
            continue
        else:
            # Handle unsupported input
            print(f"Unsupported input: {item}")
            continue


def main():
    """Main function to run the transcription process."""
    input_files = settings.input.urls_or_paths
    if input_files:
        print("Starting transcription...")
        transcribe()
    else:
        print("No input files or URLs provided.")


if __name__ == "__main__":
    main()
