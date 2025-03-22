from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from Transcriber.types.export_type import ExportType

# Get the project root directory
PROJECT_ROOT = Path.cwd()


class Input(BaseModel):
    """Configuration class for input settings.

    Parameters
    ----------
    urls_or_paths : list[str]
        List of URLs or file paths to process.
    skip_if_output_exist : bool, optional
        Skip processing if output files already exist, by default True.
    verbose : bool, optional
        Enable verbose output, by default False.
    """

    urls_or_paths: list[str] = Field(..., examples=[["."]])
    skip_if_output_exist: bool = True
    verbose: bool = False


class YtDlp(BaseModel):
    """Configuration class for YouTube-DL settings.

    Parameters
    ----------
    download_retries : int, optional
        Number of retry attempts for downloads, by default 3.
    yt_dlp_options : str | None, optional
        Additional options for yt-dlp, by default None.
    save_responses : bool, optional
        Whether to save responses from yt-dlp downloads, by default True.
    """

    download_retries: int = 3
    yt_dlp_options: str | None = None
    save_responses: bool = True


class Output(BaseModel):
    """Configuration class for output settings.

    Parameters
    ----------
    output_formats : list[str], optional
        List of desired output formats. If "all" is included, all available formats will be used.
        Default is ["all"].
    output_dir : str, optional
        Directory path where output files will be saved. Default is "Output".
    save_files_before_compact : bool, optional
        Whether to save files before compacting segments, by default False.
    min_words_per_segment : int, optional
        Minimum number of words required per segment, by default 1.
    save_yt_dlp_responses : bool, optional
        Whether to save responses from yt-dlp downloads, by default True.
    """

    output_formats: list[str] = Field(default=["all"], examples=[["txt"]])
    output_dir: str = "Transcripts"
    save_files_before_compact: bool = False
    min_words_per_segment: int = 1
    save_yt_dlp_responses: bool = True
    title_font_name: str = "Times New Roman"
    body_font_name: str = "Arial"
    title_font_size: int = 30
    body_font_size: int = 20

    @model_validator(mode="after")
    def process_formats(self) -> "Output":
        if "all" in self.output_formats:
            self.output_formats = [export_type.value for export_type in ExportType]
        if str(ExportType.ALL) in self.output_formats:
            self.output_formats.remove(str(ExportType.ALL))
        return self


class Whisper(BaseModel):
    """Whisper model configuration class.

    Parameters
    ----------
    model_name_or_path : str, optional
        Path to the model or name of the model to load.
        Default is "large-v3".
    task : str, optional
        Task to perform (transcribe or translate), by default "transcribe".
    language : str
        Target language for transcription/translation (e.g., "ar", "en").
    use_faster_whisper : bool, optional
        Whether to use the faster Whisper implementation, by default True.
    beam_size : int, optional
        Beam size for beam search decoding, by default 5.
    ct2_compute_type : str, optional
        Compute type for CTranslate2 backend (float32 or float16), by default "float16".

    Notes
    -----
    If the model name ends with ".en", the language will be automatically set to "en".
    """

    model_name_or_path: str = "large-v3"
    task: str = "transcribe"
    language: str = Field(..., examples=["ar", "en"])
    use_faster_whisper: bool = True
    beam_size: int = 5
    ct2_compute_type: str = "float16"
    use_batched_transcription: bool = True
    batch_size: int = 16
    vad_filter: bool = True
    vad_parameters: dict = dict(min_silence_duration_ms=500)

    @model_validator(mode="after")
    def set_language(self) -> "Whisper":
        if self.model_name_or_path.endswith(".en"):
            self.language = "en"
        return self


class Logging(BaseModel):
    """Configuration class for logging settings."""

    log_to_console: bool = True
    log_to_file: bool = True
    log_level: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_path: str = "logs"
    rotation: str = "1 week"
    backtrace: bool = True
    diagnose: bool = True
    # logfire settings
    enable_logfire: bool = False
    logfire_token: str | None = None


class Settings(BaseSettings):
    """Main settings class that combines all configuration components.

    Attributes
    ----------
    input : Input
        Input configuration settings.
    output : Output
        Output configuration settings.
    whisper : Whisper
        Whisper model configuration settings.
    logging : Logging
        Logging configuration settings.
    yt_dlp : YtDlp
        YouTube-DL configuration settings.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_ignore_empty=True,
        extra="ignore",
        env_nested_delimiter="__",
    )

    input: Input = Field(default_factory=Input)
    output: Output = Field(default_factory=Output)
    whisper: Whisper = Field(default_factory=Whisper)
    logging: Logging = Field(default_factory=Logging)
    yt_dlp: YtDlp = Field(default_factory=YtDlp)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
