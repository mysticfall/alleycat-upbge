from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Generic, Mapping, Optional, TypeVar

from alleycat.reactive import ReactiveObject
from dependency_injector import providers
from returns.maybe import Maybe
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


class InputMap(Lookup[Lookup[InputBinding]], LoggingSupport):

    def __init__(self, values: Mapping[str, Lookup[InputBinding]]) -> None:
        super().__init__(values)

        self.logger.info("Created an input map with %d categories: %s.", len(values), ", ".join(values.keys()))

    def find_binding(self, key: str, category: str) -> Maybe[InputBinding]:
        return self.find(category).bind(lambda c: c.find(key))

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

        def create_lookup(configs) -> Lookup[InputBinding]:
            bindings = dict()

            for k in configs:
                binding_config = configs[k]

                if "type" not in binding_config:
                    logger.warning("Missing type information for input binding: '%s'.", k)
                    continue

                binding_type = binding_config["type"]
                binding = binding_factory(binding_type, input_factory, binding_config)

                logger.debug("Adding binding '%s' as '%s'.", binding, k)

                bindings[k] = binding

            logger.debug("Configured %d binding: %s.", len(bindings), ", ".join(bindings.keys()))

            return Lookup[InputBinding](bindings)

        lookups = dict()

        for key in config:
            logger.debug("Found input category '%s'.", key)

            lookup = create_lookup(config[key])

            lookups[key] = lookup

        return InputMap(lookups)
