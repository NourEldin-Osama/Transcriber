from pathlib import Path

from Transcriber.config import settings

LOG_DIR = Path(settings.logging.log_path)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOGURU_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS Z}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
