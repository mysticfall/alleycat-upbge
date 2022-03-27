from abc import ABC
from logging import Logger


class LoggingSupport(ABC):
    logger: Logger
