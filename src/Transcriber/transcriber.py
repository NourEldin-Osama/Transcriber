from pathlib import Path
from typing import Any

from Transcriber.config import LOG_LEVELS, settings, update_settings
from Transcriber.export_handlers.exporter import Writer
from Transcriber.logging import logfire, logger
from Transcriber.source_loaders.downloader import Downloader
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
    filtered_media_files = file_utils.filter_media_files([path] if path.is_file() else list(path.iterdir()))
    files: list[dict[str, Any]] = [{"file_name": file.name, "file_path": file} for file in filtered_media_files]

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
                if settings.input.skip_if_output_exist and writer.is_output_exist(file_name):
                    logger.info(
                        f"Skipping existing file: {file_name}",
                    )
                    progress.advance(total_task)
                    continue

                file_path = str(file["file_path"].absolute())

                with logfire.span(f"Transcribing {file_name}"):
                    recognizer = WhisperRecognizer(progress=progress)
                    segments = recognizer.recognize(
                        file_path,
                        model,
                    )

                if not segments:
                    logger.warning(f"No segments returned for file: {file_name}")
                else:
                    logger.success(f"Successfully transcribed file: {file_name}")
                    writer.write_all(file_name, segments)
            except Exception:
                logger.exception(f"Error processing file {file_name}")
            finally:
                progress.advance(total_task)

        progress.update(
            total_task,
            description="[green]Transcription Complete 🎉",
        )


def should_skip(element: dict[str, Any]) -> bool:
    """
    Determine if an element from a playlist should be skipped.

    Args:
        element: Dictionary containing metadata about the video/audio

    Returns:
        bool: True if the element should be skipped, False otherwise
    """
    return (
        element.get("title") == "[Private video]"
        or element.get("title") == "[Deleted video]"
        or ("availability" in element and element["availability"] == "subscriber_only")
        or ("live_status" in element and element["live_status"] == "is_upcoming")
    )


def process_url(url: str, model):
    """
    Process a URL by downloading its audio content and transcribing it.

    Args:
        url: URL to process
        model: Whisper model for transcription
    """
    # Get the download directory
    download_dir = settings.yt_dlp.download_dir
    download_dir.mkdir(parents=True, exist_ok=True)

    # Initialize the downloader
    yt_dlp_options = settings.yt_dlp.yt_dlp_options or "{}"
    downloader = Downloader(
        yt_dlp_options=yt_dlp_options,
        output_dir=str(download_dir),
    )

    # Download the content
    url_data = downloader.download(
        url,
        retries=settings.yt_dlp.download_retries,
        save_response=settings.yt_dlp.save_responses,
    )

    # Prepare elements list for processing
    elements = extract_elements_from_url_data(url_data)

    total_elements = len(elements)
    logger.info(
        "Processing {elements_count} elements from URL",
        elements_count=total_elements,
    )

    # Skip processing if no elements found
    if total_elements == 0:
        logger.warning(f"⚠️ No media found in URL: {url}")
        return

    process_url_elements(elements, model, download_dir)


def extract_elements_from_url_data(url_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract elements from URL data obtained from YouTube-DL.

    Args:
        url_data: Data obtained from YouTube-DL

    Returns:
        list: List of elements to process
    """
    elements = [url_data]
    if url_data.get("_type", "") == "playlist":
        entries = url_data["entries"]
        elements = []
        for entry in entries:
            if entry is None:
                continue
            if entry.get("_type", "") == "playlist":
                elements.extend(entry.get("entries", []))
            else:
                elements.append(entry)
        elements = list(filter(lambda element: element is not None, elements))
    return elements


def process_url_elements(elements: list[dict[str, Any]], model, download_dir: Path) -> None:
    """
    Process URL elements by transcribing them.

    Args:
        elements: List of elements (videos/audios) to process
        model: Whisper model for transcription
        download_dir: Directory where downloaded files are stored
    """
    total_elements = len(elements)

    with (
        MultipleProgress() as progress,
        logfire.span("Transcribing", description=f"Transcribing {total_elements} elements from URL"),
    ):
        total_task = progress.add_task(
            f"[bold blue]Transcribing {total_elements} elements",
            total=total_elements,
            progress_type="total",
        )

        for element in elements:
            try:
                # Skip certain types of videos
                if should_skip(element):
                    logger.info(f"Skipping element: {element.get('title', 'Unknown')}")
                    progress.advance(total_task)
                    continue

                # Initialize the writer
                writer = Writer()
                element_id = element["id"]

                # Skip if output already exists and skip_if_output_exist is True
                if settings.input.skip_if_output_exist and writer.is_output_exist(element_id):
                    logger.info(f"Skipping existing element: {element_id}")
                    progress.advance(total_task)
                    continue

                # Get the file path for the downloaded audio
                file_path = download_dir / f"{element_id}.mp3"

                # Transcribe the audio
                with logfire.span(f"Transcribing {element.get('title', element_id)}"):
                    recognizer = WhisperRecognizer(progress=progress)
                    segments = recognizer.recognize(
                        str(file_path),
                        model,
                    )

                # Write the transcription
                if not segments:
                    logger.warning(f"No segments returned for element: {element_id}")
                else:
                    logger.success(f"Successfully transcribed element: {element_id}")
                    writer.write_all(element_id, segments)
            except Exception as e:
                logger.exception(f"Error processing element: {element.get('id', 'Unknown')}, Error: {e!s}")
            finally:
                progress.advance(total_task)

        progress.update(
            total_task,
            description="[green]URL Transcription Complete 🎉",
        )


def transcribe(
    urls_or_paths: list[str] | None = None,
    output_dir: str | None = None,
    output_formats: list[str] | None = None,
    language: str | None = None,
    log_level: LOG_LEVELS | None = None,
    enable_logfire: bool | None = None,
    logfire_token: str | None = None,
    download_dir: str | None = None,
):
    """
    Main transcription function that processes all input sources.

    Args:
        urls_or_paths: List of URLs or local paths to process.
        output_dir: Directory where transcription outputs will be saved.
        output_formats: List of output formats for the transcription results.
        language: Language to use for transcription.
        log_level: Logging level for the application.
        enable_logfire: Whether to enable Logfire for logging.
        logfire_token: Token for authenticating with Logfire.
        download_dir: Directory where downloaded files will be stored.
    """
    update_settings(
        urls_or_paths=urls_or_paths,
        output_dir=output_dir,
        output_formats=output_formats,
        language=language,
        log_level=log_level,
        enable_logfire=enable_logfire,
        logfire_token=logfire_token,
        download_dir=download_dir,
    )
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
            logger.info(f"Processing URL: {item}")
            process_url(item, model)
        else:
            # Handle unsupported input
            logger.warning(f"Unsupported input: {item}")
