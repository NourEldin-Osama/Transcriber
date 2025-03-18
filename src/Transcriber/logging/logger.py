from pathlib import Path

import logfire
from loguru import logger

from Transcriber.config import settings

logfire.configure()
logfire.instrument_pydantic()

LOG_DIR = Path(settings.logging.log_path)
LOG_DIR.mkdir(parents=True, exist_ok=True)

if not settings.logging.log_to_console:
    # Remove the default console handler
    logger.remove()

logger.configure(handlers=[logfire.loguru_handler()])

if settings.logging.log_to_file:
    # Add file handler for all logs
    logger.add(
        LOG_DIR / "transcriber.log",
        level=settings.logging.log_level,
        rotation=settings.logging.rotation,
        backtrace=settings.logging.backtrace,
        diagnose=settings.logging.diagnose,
    )

    # Add file handler for errors only
    logger.add(
        LOG_DIR / "transcriber_errors.log",
        level="ERROR",
        rotation=settings.logging.rotation,
        backtrace=settings.logging.backtrace,
        diagnose=settings.logging.diagnose,
    )

logger.debug("Settings", settings=settings)
logger.info("Logging initialized")
