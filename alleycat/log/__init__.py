# noinspection PyUnresolvedReferences
import logging
from logging import Logger
from typing import Any

from validator_collection import not_empty

from .console import ConsoleLogger
from .support import LoggingSupport


def get_logger_name(obj: Any, drop_last_path: bool = True) -> str:
    not_empty(obj)

    name = obj.__qualname__ if isinstance(obj, type) else type(obj).__qualname__
    segments = obj.__module__.split(".")

    index = -1 if drop_last_path else len(segments)

    return ".".join(segments[:index] + [name])


def get_logger(obj: Any) -> Logger:
    return logging.getLogger(get_logger_name(obj))
