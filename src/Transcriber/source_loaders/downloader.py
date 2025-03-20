import json
import os
from typing import Any

import yt_dlp


class Downloader:
    """
    A class for downloading and processing audio content from various online sources using yt-dlp.
    This class handles the downloading of audio content, managing download history,
    and processing of both single files and playlists. It provides functionality for
    retrying failed downloads and saving response data.
    Attributes:
        yt_dlp_options (str): JSON string containing custom options for yt-dlp configuration
        youtube_dl_with_archive: YoutubeDL instance that tracks download history
        youtube_dl_without_archive: YoutubeDL instance that doesn't track download history
        ```python
        downloader = Downloader(
            yt_dlp_options='{"format": "bestaudio"}',
            output_dir='downloads'
        result = downloader.download('https://www.youtube.com/watch?v=example')
        ```
    """

    def __init__(self, yt_dlp_options: str, output_dir: str):
        """
        Initialize a source loader with YouTube-DL configuration.
        Args:
            yt_dlp_options (str): Options string for yt-dlp configuration
            output_dir (str): Directory path where downloaded files will be saved
        Description:
            Creates a new loader instance and initializes two YouTube-DL configurations:
            - One with download archive tracking
            - One without download archive tracking
        The configurations are used for different download scenarios based on whether
        history tracking is needed.
        """
        self.yt_dlp_options = yt_dlp_options
        self.output_dir = output_dir

        self._initialize_youtube_dl_with_archive()
        self._initialize_youtube_dl_without_archive()

    def download(self, url: str, retries: int = 3, save_response: bool = False) -> dict[str, Any]:
        """Downloads and extracts information from a given URL using youtube-dl.
        This method attempts to download content from the provided URL and extract its information.
        It includes a retry mechanism for failed attempts and an option to save the response data.
        Args:
            url (str): The URL to download content from
            retries (int, optional): Number of retry attempts if download fails. Defaults to 3.
            save_response (bool, optional): Whether to save the extracted information to a file. Defaults to False.
        Returns:
            dict[str, Any]: Dictionary containing the extracted information from the URL
        Example:
            url_data = loader.download("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        """
        while True:
            self.youtube_dl_with_archive.download(url)
            url_data = self.youtube_dl_without_archive.extract_info(url, download=False)

            if retries <= 0 or not self._should_retry(url_data):
                break

            self._initialize_youtube_dl_with_archive()
            retries -= 1

        if save_response:
            self._save_response(url_data)

        return url_data

    def _initialize_youtube_dl_with_archive(self) -> None:
        """
        Initializes a YoutubeDL instance with download archive functionality.

        The archive file keeps track of previously downloaded videos to avoid re-downloading.
        The archive is stored in 'archive.txt' within the output directory.

        Returns:
            None
        """
        self.youtube_dl_with_archive = yt_dlp.YoutubeDL(
            self._config(
                download_archive=os.path.join(self.output_dir, "archive.txt"),
            )
        )

    def _initialize_youtube_dl_without_archive(self) -> None:
        """
        Initializes a youtube-dl instance without archive functionality.

        This method creates a new instance of youtube-dl without using download archives,
        allowing for re-downloading of previously downloaded content. It configures the
        youtube-dl instance with extract_flat=True to only extract video metadata without
        downloading the actual video content.

        Returns:
            None
        """
        self.youtube_dl_without_archive = yt_dlp.YoutubeDL(self._config(extract_flat=True))

    def _config(self, **kwargs: Any) -> dict[str, Any]:
        """Configure YouTube downloader options.
        Generates a configuration dictionary for yt-dlp with audio extraction settings.
        Default configuration extracts the best available audio stream and converts it to MP3.
        Args:
            **kwargs: Additional keyword arguments to override default configuration.
        Returns:
            dict[str, Any]: Configuration dictionary containing yt-dlp options with the following defaults:
                - extract_audio: True (extracts audio from video)
                - format: 'bestaudio' (selects best audio quality)
                - ignoreerrors: True (continues on download errors)
                - outtmpl: Output template for saving files
                - postprocessors: FFmpeg settings for MP3 conversion
                - quiet: True (minimal console output)
                - verbose: False (no debug output)
        Note:
            Configuration can be further customized via kwargs and self.yt_dlp_options JSON string.
        """
        config = {
            "extract_audio": True,
            "format": "bestaudio",
            "ignoreerrors": True,
            "outtmpl": os.path.join(self.output_dir, "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                },
            ],
            "quiet": True,
            "verbose": False,
        }

        config.update(kwargs)
        config.update(json.loads(self.yt_dlp_options))

        return config

    def _should_retry(self, url_data: dict[str, Any]) -> bool:
        """
        Determines if downloading should be retried based on URL data and existing files.
        This method checks whether audio files need to be downloaded by verifying their existence
        in the output directory. For playlists, it checks all entries. For single items, it checks
        the individual file.
        Args:
            url_data (dict[str, Any]): Dictionary containing URL metadata, including information
                about audio files or playlists to be downloaded.
        Returns:
            bool: True if any file needs to be downloaded (doesn't exist), False if all files exist.
        """

        def file_exists(file_name: str) -> bool:
            extensions = ["mp3", "wav", "m4a", "webm", "opus"]

            return any(os.path.exists(os.path.join(self.output_dir, f"{file_name}.{ext}")) for ext in extensions)

        if "_type" in url_data and url_data["_type"] == "playlist":
            for entry in url_data["entries"]:
                if entry and not file_exists(entry["id"]):
                    return True
        else:
            if not file_exists(url_data["id"]):
                return True

        return False

    def _save_response(self, url_data: dict[str, Any]) -> None:
        """
        Saves the provided URL data to a JSON file in the output directory.
        This method handles both single videos and playlists. For playlists, it processes each entry individually.
        Before saving, it removes any post-processors from the requested downloads.
        Args:
            url_data (dict[str, Any]): Dictionary containing the URL metadata and download information.
                                       For playlists, includes 'entries' list of individual videos.
        Returns:
            None
        Side Effects:
            - Creates or overwrites a JSON file in the output directory named '{id}.json'
            - Removes postprocessors from requested_downloads in the url_data
        """
        if "_type" in url_data and url_data["_type"] == "playlist":
            for entry in url_data["entries"]:
                if entry and "requested_downloads" in entry:
                    self._remove_postprocessors(entry["requested_downloads"])
        elif "requested_downloads" in url_data:
            self._remove_postprocessors(url_data["requested_downloads"])

        file_path = os.path.join(self.output_dir, f"{url_data['id']}.json")

        with open(file_path, "w", encoding="utf-8") as fp:
            json.dump(url_data, fp, indent=2, ensure_ascii=False)

    def _remove_postprocessors(self, requested_downloads: list[dict[str, Any]]) -> None:
        """
        Removes postprocessor settings from download requests.

        This method removes the '__postprocessors' key from each download request dictionary
        in the provided list. This is typically used to clean up download configurations
        before processing.

        Args:
            requested_downloads: A list of dictionaries containing download request configurations.
                Each dictionary may contain a '__postprocessors' key that will be removed.

        Returns:
            None
        """
        for requested_download in requested_downloads:
            requested_download.pop("__postprocessors")
