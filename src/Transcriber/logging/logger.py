"""Logging module for Transcriber."""

import sys

from loguru import logger

from Transcriber.config import settings
from Transcriber.logging.config import LOG_DIR


def configure_console_logging() -> None:
    """Configure logging to console if enabled in settings."""
    if not settings.logging.log_to_console:
        return
    # Add console handler for all logs
    logger.add(sys.stderr, level=settings.logging.log_level)


def configure_file_logging() -> None:
    """Configure logging to files if enabled in settings."""
    if not settings.logging.log_to_file:
        return

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
        backtrace=True,
        diagnose=True,
    )


def get_dummy_logfire() -> object:
    """
    Returns a dummy logfire implementation for compatibility.

    Returns:
        object: Dummy logfire implementation
    """
    from Transcriber.logging.dummy_logfire import DummyLogfire

    logger.warning("Logfire is not enabled. Using dummy logfire.")
    # Return a dummy logfire implementation
    # for compatibility with the rest of the code
    return DummyLogfire()


def get_logfire() -> object:
    """
    Configure and return the LogFire module if enabled in settings.
    If LogFire is not enabled or fails to import, return a dummy implementation.
    This function is used to set up LogFire for logging.

    Returns:
        object: LogFire module if configured successfully, or a dummy implementation.
    """
    if not settings.logging.enable_logfire:
        logger.info("Logfire is not enabled in settings")
        return get_dummy_logfire()

    try:
        import logfire

        if settings.logging.logfire_token:
            # Initialize logfire with the token
            logfire.configure(
                token=settings.logging.logfire_token,
                console=False,
            )
        else:
            # Initialize logfire without a token
            logfire.configure(console=False)

        logfire.instrument_pydantic()
        logfire_sink = logfire.loguru_handler()["sink"]
        logger.add(logfire_sink, level="TRACE")
        logger.info("Logfire configured successfully.")
        return logfire

    except ImportError:
        logger.warning("Logfire is not installed. Please install it to use logfire logging.")
        return get_dummy_logfire()
    except Exception as e:
        logger.error(f"Failed to configure logfire: {e}. Please check your logfire configuration.")
        return get_dummy_logfire()


# Initialize and configure all logging components when the module is imported

# Remove the default console handler
logger.remove()

# Configure logging components
configure_console_logging()
configure_file_logging()

# Configure LogFire
logfire = get_logfire()

# Log initialization
logger.debug("Settings", settings=settings)
logger.info("Logging initialized")
