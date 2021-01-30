from abc import ABC
from functools import cached_property, partial
from logging import Logger, getLogger

from alleycat import log
from alleycat.common import ErrorHandler, ErrorHandlerSupport


class LoggingSupport(ErrorHandlerSupport, ABC):

    def __init__(self) -> None:
        super().__init__()

    @property
    def logger_name(self) -> str:
        return log.get_logger_name(self)

    @cached_property
    def logger(self) -> Logger:
        return getLogger(self.logger_name)

    @property
    def error_handler(self) -> ErrorHandler:
        return partial(self.logger.exception, "Unhandled exception occurred.")
