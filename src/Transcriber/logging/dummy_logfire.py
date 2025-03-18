from typing import Any


# Create dummy logfire context manager
class DummySpan:
    def __init__(self, *args: Any, **kwargs: Any):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *args: Any):
        pass


class DummyLogfire:
    def span(self, *args: Any, **kwargs: Any):
        return DummySpan(*args, **kwargs)
