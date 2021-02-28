from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Generic, Mapping, Optional, Sequence, TypeVar, Union

from alleycat.reactive import ReactiveObject
from dependency_injector import providers
from returns.maybe import Maybe, Nothing
from validator_collection.validators import not_empty

from alleycat import log
from alleycat.common import Lookup
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


class InputMap(Lookup[Any], LoggingSupport):

    def __init__(self, values: Mapping[str, Lookup[InputBinding]]) -> None:
        super().__init__(values)

        self.logger.info("Created an input map with %d categories: %s.", len(values), ", ".join(values.keys()))

    def find_binding(self, path: Union[str, Sequence[str]]) -> Maybe[InputBinding]:
        if isinstance(not_empty(path), str):
            return self._resolve((path,))

        return self._resolve(path)

    def _resolve(self, path: Sequence[str]) -> Maybe[InputBinding]:
        if len(path) == 0:
            return Nothing

        return self.find(path[0]).bind(lambda i: i if isinstance(i, InputBinding) else self._resolve(path[1:]))

    @classmethod
    def from_config(cls,
                    binding_factory: providers.Provider[InputBinding],
                    input_factory: providers.Provider[Input],
                    config: Mapping[str, Any]) -> InputMap:
        not_empty(binding_factory)
        not_empty(input_factory)
        not_empty(config)

        logger = log.get_logger(cls)

        logger.debug("Creating an input map from config: %s.", config)

        def create_lookup(configs) -> Lookup:
            items = dict()

            for k in configs:
                value = configs[k]

                if "type" in value:
                    binding_type = value["type"]
                    binding = binding_factory(binding_type, input_factory, value)

                    logger.debug("Adding binding '%s' as '%s'.", binding, k)

                    items[k] = binding
                elif isinstance(value, Mapping):
                    logger.debug("Adding sub categories with key '%s'.", k)

                    items[k] = create_lookup(value)
                else:
                    logger.warning("Ignoring an invalid entry '%s'.", k)

            logger.debug("Configured %d lookup entries: %s.", len(items), ", ".join(items.keys()))

            return Lookup(items)

        lookups = dict()

        for key in config:
            logger.debug("Found input category '%s'.", key)

            lookup = create_lookup(config[key])

            lookups[key] = lookup

        return InputMap(lookups)
