"""Transcriber - A tool to transcribe audio files using Whisper models."""

import importlib.metadata
from Transcriber import transcriber, config

__version__ = importlib.metadata.version("Transcriber")
__all__ = ["transcriber", "config"]
