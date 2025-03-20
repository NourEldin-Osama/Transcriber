from pathlib import Path

from Transcriber.config import settings

LOG_DIR = Path(settings.logging.log_path)
LOG_DIR.mkdir(parents=True, exist_ok=True)
