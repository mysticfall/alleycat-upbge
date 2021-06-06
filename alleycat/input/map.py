from __future__ import annotations

from typing import Any, Mapping, Sequence, cast

from alleycat.reactive import functions as rv
from dependency_injector import providers
from returns.converters import maybe_to_result
from returns.maybe import Maybe, Nothing, Some
from returns.methods import cond
from returns.result import ResultE
from rx import Observable
from validator_collection.validators import not_empty

from alleycat import log
from alleycat.common import Lookup
from alleycat.input import Input, InputBinding
from alleycat.log import LoggingSupport


class InputMap(Lookup[Any], LoggingSupport):

    def __init__(self, values: Mapping[str, Lookup[InputBinding]]) -> None:
        super().__init__(values)

        self.logger.info("Created an input map with %d categories: %s.", len(values), ", ".join(values.keys()))

    def find_binding(self, path: str) -> Maybe[InputBinding]:
        segments = not_empty(path).split("/")

        def resolve(p: Sequence[str], lookup: Any) -> Maybe[Any]:
            if not isinstance(lookup, Lookup):
                return Nothing

            return lookup.find(p[0]).bind(lambda i: Some(i) if len(p) == 1 else resolve(p[1:], i))

        return resolve(segments, self).bind(lambda i: cond(Maybe, isinstance(i, InputBinding), i))

    def require_binding(self, path: str) -> ResultE[InputBinding]:
        # noinspection PyTypeChecker
        return maybe_to_result(self.find_binding(path)) \
            .alt(lambda _: ValueError(f"Unknown input path: '{path}'."))

    def observe(self, path: str) -> ResultE[Observable]:
        return self.require_binding(path).map(lambda b: rv.observe(b.value))

    @classmethod
    def from_config(cls,
                    binding_factory: providers.Provider[InputBinding],
                    input_factory: providers.Provider[Input],
                    config: Mapping[str, Any]) -> InputMap:
        not_empty(binding_factory)
        not_empty(input_factory)
        not_empty(config, allow_empty=True)

        logger = log.get_logger(cls)

        logger.debug("Creating an input map from config: %s.", config)

        def create_lookup(configs, factory=Lookup) -> Lookup:
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

            return factory(items)

        return cast(InputMap, create_lookup(config, InputMap))
