from .types.export_type import ExportType

from functools import lru_cache
from pathlib import Path
from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, BaseModel

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class Input(BaseModel):
    urls_or_paths: list[str]
    skip_if_output_exist: bool
    download_retries: int
    yt_dlp_options: str
    verbose: bool


class Output(BaseModel):
    """Configuration class for output settings.
    This class manages configuration settings related to transcription output,
    including formats, directory paths, and segment management.
    Parameters
    ----------
    output_formats : list[str]
        List of desired output formats. If "all" is included, all available formats will be used.
    output_dir : str
        Directory path where output files will be saved.
    save_files_before_compact : bool
        Whether to save files before compacting segments.
    min_words_per_segment : int
        Minimum number of words required per segment.
    save_yt_dlp_responses : bool
        Whether to save responses from yt-dlp downloads.
    Attributes
    ----------
    output_formats : list[str]
        Processed list of output formats.
    output_dir : str
        Directory path for output files.
    save_files_before_compact : bool
        Flag for saving files before compaction.
    min_words_per_segment : int
        Minimum word count per segment.
    save_yt_dlp_responses : bool
        Flag for saving yt-dlp responses.
    """

    output_formats: list[str] = Field(default=["all"])
    output_dir: str = ""
    save_files_before_compact: bool = False
    min_words_per_segment: int = 1
    save_yt_dlp_responses: bool = True

    @model_validator(mode="after")
    def process_formats(self) -> "Output":
        if "all" in self.output_formats:
            self.output_formats = [export_type.value for export_type in ExportType]
        if str(ExportType.ALL) in self.output_formats:
            self.output_formats.remove(str(ExportType.ALL))
        return self


class Whisper(BaseModel):
    """Whisper model configuration class.
    This class manages configuration parameters for the Whisper speech recognition model.
    Args:
        model_name_or_path (str): Path to the model or name of the model to load.
        task (str): Task to perform (e.g., "transcribe", "translate").
        language (str): Target language for transcription/translation (e.g., "ar", "en").
        use_faster_whisper (bool): Whether to use the faster Whisper implementation.
        beam_size (int): Beam size for beam search decoding.
        ct2_compute_type (str): Compute type for CTranslate2 backend (e.g., "float32", "float16").
    Note:
        If the model name ends with ".en", the language will be automatically set to "en".
    """

    model_name_or_path: str
    task: str
    language: str
    use_faster_whisper: bool
    beam_size: int
    ct2_compute_type: str

    @model_validator(mode="after")
    def set_language(self) -> "Whisper":
        if self.model_name_or_path.endswith(".en"):
            self.language = "en"
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), env_ignore_empty=True, extra="ignore"
    )

    input: Input
    output: Output
    whisper: Whisper


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
