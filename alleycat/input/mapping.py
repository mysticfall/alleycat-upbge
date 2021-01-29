from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Generic, Mapping, Optional, TypeVar

from alleycat.reactive import ReactiveObject
from dependency_injector import providers
from returns.maybe import Maybe
from validator_collection.validators import not_empty

from alleycat.common import Lookup
from alleycat.input import Input

T = TypeVar("T", bound=Input)


class InputBinding(Generic[T], ReactiveObject, ABC):

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        self._name = not_empty(name)
        self._description = Maybe.from_optional(description)

        super().__init__()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> Maybe[str]:
        return self._description

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[{self.name}]"


class InputMap(Lookup[Lookup[InputBinding]]):

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

        logger = logging.getLogger(cls.__name__)

        def create_lookup(configs) -> Lookup[InputBinding]:
            bindings = dict()

            for k in configs:
                binding_config = configs[k]

                if "type" not in binding_config:
                    logger.warning("Missing type information for input binding: '%s'.", k)
                    continue

                binding_type = binding_config["type"]
                binding = binding_factory(binding_type, input_factory, binding_config)

                bindings[k] = binding

            return Lookup[InputBinding](bindings)

        lookups = dict()

        for key in config:
            lookup = create_lookup(config[key])

            lookups[key] = lookup

        return InputMap(lookups)
