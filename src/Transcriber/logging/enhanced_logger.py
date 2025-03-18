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
