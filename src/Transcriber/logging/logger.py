from pathlib import Path

from Transcriber.config import settings

LOG_DIR = Path(settings.logging.log_path)
LOG_DIR.mkdir(parents=True, exist_ok=True)

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
    from typing import Any

    # Setup basic logger with enhanced interface
    class EnhancedLogger(logging.Logger):
        def __init__(self, name: str):
            super().__init__(name)

        def _format_message(self, msg: str, kwargs: dict[str, Any]) -> str:
            if kwargs:
                # Convert kwargs to a string representation
                kwargs_str = ", ".join(f"{k} = {v}" for k, v in kwargs.items())
                return f"{msg} {kwargs_str}"
            return msg

        def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
            msg = self._format_message(msg, kwargs)
            super().info(f"ℹ️  {msg}", *args)

        def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
            msg = self._format_message(msg, kwargs)
            super().debug(msg, *args)

        def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
            msg = self._format_message(msg, kwargs)
            super().warning(f"⚠️  {msg}", *args)

        def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
            msg = self._format_message(msg, kwargs)
            super().error(f"❌  {msg}", *args)

        def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
            msg = self._format_message(msg, kwargs)
            super().critical(f"🚨  {msg}", *args)

        def success(self, msg: str, *args: Any, **kwargs: Any) -> None:
            self.info(f"✅  {msg}", *args, **kwargs)

        def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
            self.debug(msg, *args, **kwargs)

    # Register our enhanced logger class
    logging.setLoggerClass(EnhancedLogger)

    # Create logger instance
    logger = logging.getLogger(__name__)
    logger.setLevel(settings.logging.log_level)

    # Create formatters and handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if settings.logging.log_to_file:
        # Add file handler for all logs
        file_handler = logging.FileHandler(LOG_DIR / "transcriber.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add file handler for errors only
        error_handler = logging.FileHandler(LOG_DIR / "transcriber_errors.log", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    if settings.logging.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Create dummy logfire context manager
    class DummySpan:
        def __init__(self, *args: Any, **kwargs: Any):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: Any):
            pass

    class DummyLogfire:
        def span(self, *args: Any, **kwargs: Any):
            return DummySpan()

    logfire = DummyLogfire()


logger.debug("Settings", settings=settings)
logger.info("Logging initialized")
