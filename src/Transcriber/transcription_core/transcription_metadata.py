import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import humanize

from Transcriber.config import settings


class TranscriptionMetadata:
    """Stores metadata about a transcription job."""

    def __init__(
        self,
        file_name: str,
        file_path: str,
        status: str,
        duration: float,
        processing_time: float,
    ):
        """
        Initialize transcription metadata.

        Args:
            file_name: Name of the processed audio file
            file_path: Path to the processed audio file
            status: Status of the processing (success/fail)
            duration: Duration of the audio in seconds
            processing_time: Time taken to process the audio in seconds
        """
        self.file_name = file_name
        self.status = status
        self.duration = duration
        self.processing_time = processing_time
        self.file_size = Path(file_path).stat().st_size
        self.date_time = datetime.now(UTC)
        self.append_to_csv()

    def to_csv(self):
        """
        Append the metadata to a CSV file.
        """
        self.metadata = {
            "File Name": self.file_name,
            "Status": self.status,
            "Duration": humanize.precisedelta(
                timedelta(seconds=self.duration),
            ),
            "Processing Time": humanize.precisedelta(
                timedelta(seconds=self.processing_time),
            ),
            "File Size": humanize.naturalsize(self.file_size),
            "Duration (seconds)": self.duration,
            "Processing Time (seconds)": self.processing_time,
            "File Size (bytes)": self.file_size,
            "Date Time": self.date_time,
        }

    def append_to_csv(self):
        """
        Append the metadata to a CSV file.
        """
        self.to_csv()
        with open(settings.logging.metadata_csv_path, "a") as file:
            writer = csv.DictWriter(file, fieldnames=self.metadata.keys())
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(self.metadata)
