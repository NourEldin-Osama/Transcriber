from Transcriber.config import settings
from Transcriber.logging.config import DEFAULT_FORMAT, LOG_DIR

try:
    import logfire
    from loguru import logger

    logfire.configure()
    logfire.instrument_pydantic()

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


except ImportError:
    import logging

    from Transcriber.logging.dummy_logfire import DummyLogfire
    from Transcriber.logging.enhanced_logger import EnhancedLogger

    # Register enhanced logger class
    logging.setLoggerClass(EnhancedLogger)

    # Create logger instance
    logger = logging.getLogger(__name__)
    logger.setLevel(settings.logging.log_level)

    # Create formatters and handlers
    formatter = logging.Formatter(DEFAULT_FORMAT)

    if settings.logging.log_to_file:
        # Add file handler for all logs
        file_handler = logging.FileHandler(
            LOG_DIR / "transcriber.log", encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add file handler for errors only
        error_handler = logging.FileHandler(
            LOG_DIR / "transcriber_errors.log", encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    if settings.logging.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logfire = DummyLogfire()


logger.debug("Settings", settings=settings)
logger.info("Logging initialized")
