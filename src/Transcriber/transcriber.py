from pathlib import Path
from typing import Any

from Transcriber.config import settings
from Transcriber.export_handlers.exporter import Writer
from Transcriber.logging import logfire, logger
from Transcriber.transcription_core.whisper_recognizer import WhisperRecognizer
from Transcriber.utils import file_utils
from Transcriber.utils.progress import MultipleProgress
from Transcriber.utils.whisper import whisper_utils


def prepare_output_directory():
    """Prepare the output directory by creating it if it does not exist."""
    output_dir = Path(settings.output.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # # Create format-specific output directory
    for output_format in settings.output.output_formats:
        format_output_dir = output_dir / output_format
        format_output_dir.mkdir(exist_ok=True)

    logger.info("Created output directory", output_dir=str(output_dir))


def process_local_directory(path, model):
    filtered_media_files = file_utils.filter_media_files(
        [path] if path.is_file() else list(path.iterdir())
    )
    files: list[dict[str, Any]] = [
        {"file_name": file.name, "file_path": file} for file in filtered_media_files
    ]

    total_files = len(files)
    # Check if there are any files to process
    if total_files == 0:
        logger.warning(f"⚠️ No media files found in {path}.")
        # Display a message to the user
        return

    logger.info(
        "Processing {files_count} media files from {path}",
        files_count=total_files,
        path=path,
    )

    with (
        MultipleProgress() as progress,
        logfire.span("Transcribing", description=f"Transcribing {total_files} files"),
    ):
        total_task = progress.add_task(
            f"[bold blue]Transcribing {total_files} files",
            total=total_files,
            progress_type="total",
        )

        for file in files:
            try:
                writer = Writer()
                file_name = Path(file["file_name"]).stem
                if settings.input.skip_if_output_exist and writer.is_output_exist(
                    file_name
                ):
                    logger.info(
                        f"Skipping existing file: {file_name}",
                    )
                    progress.advance(total_task)
                    continue

                file_path = str(file["file_path"].absolute())

                logger.info(f"Transcribing file: {file_name}")

                with logfire.span("Transcribing {file_name}", file_name):
                    recognizer = WhisperRecognizer(
                        verbose=settings.input.verbose, progress=progress
                    )
                    segments = recognizer.recognize(
                        file_path,
                        model,
                    )

                if not segments:
                    logger.warning(f"No segments returned for file: {file_name}")
                else:
                    logger.success(f"Successfully transcribed file: {file_name}")
                    writer.write_all(file_name, segments)
            except Exception as e:
                logger.error(f"Error processing file {file_name}")
            finally:
                progress.advance(total_task)

        progress.update(
            total_task,
            description="[green]Transcription Complete 🎉",
        )


def transcribe():
    """Main transcription function that processes all input sources."""
    input_files = settings.input.urls_or_paths
    if not input_files:
        logger.warning("No input files provided. Exiting transcription.")
        return
    logger.info("Starting transcription...")
    # Initialize the output directory and Whisper model
    prepare_output_directory()
    model = whisper_utils.load_model()
    logger.debug("Loaded Whisper model")

    for item in settings.input.urls_or_paths:
        if Path(item).exists():
            # Handle local file or directory input
            logger.info(f"Processing local path: {item}")
            process_local_directory(Path(item), model)

        elif item.startswith("http") or item.startswith("www"):
            # Handle URL input
            # Placeholder for URL processing logic
            logger.info(f"Processing URL: {item}")
            continue
        else:
            # Handle unsupported input
            logger.warning(f"Unsupported input: {item}")
            continue
