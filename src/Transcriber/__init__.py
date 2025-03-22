"""Transcriber - A tool to transcribe audio files using Whisper models."""

import importlib.metadata

from Transcriber import config, transcriber
from Transcriber.config import update_settings
from Transcriber.transcriber import transcribe

__version__ = importlib.metadata.version("Transcriber")
__all__ = ["config", "transcribe", "transcriber", "update_settings"]
