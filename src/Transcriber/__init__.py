"""Transcriber - A tool to transcribe audio files using Whisper models."""

import importlib.metadata

from Transcriber import config, transcriber

__version__ = importlib.metadata.version("Transcriber")
__all__ = ["config", "transcriber"]
