import logging
from abc import ABC
from typing import Generic, Optional, TypeVar

from alleycat.reactive import ReactiveObject
from returns.maybe import Maybe
from validator_collection.validators import not_empty

from alleycat.input import Input
from alleycat.log import LoggingSupport

T = TypeVar("T", bound=Input)


class InputBinding(Generic[T], LoggingSupport, ReactiveObject, ABC):

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        self._name = not_empty(name)
        self._description = Maybe.from_optional(description)

        super().__init__()

        self.logger.info("Created an input binding: '%s' (description=%s).", name, description)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> Maybe[str]:
        return self._description

    @property
    def logger_name(self) -> str:
        return ".".join((super().logger_name, self.name))

    def log_value(self, value: T) -> None:
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Binding value: %s.", value)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.name}]"

    def dispose(self) -> None:
        self.logger.info("Disposing input binding.")

        super().dispose()
