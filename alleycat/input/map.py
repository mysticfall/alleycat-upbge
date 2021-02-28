from __future__ import annotations

from typing import Any, Mapping, Sequence, Union

from dependency_injector import providers
from returns.maybe import Maybe, Nothing, Some
from validator_collection.validators import not_empty

from alleycat import log
from alleycat.common import Lookup
from alleycat.input import Input, InputBinding
from alleycat.log import LoggingSupport


class InputMap(Lookup[Any], LoggingSupport):

    def __init__(self, values: Mapping[str, Lookup[InputBinding]]) -> None:
        super().__init__(values)

        self.logger.info("Created an input map with %d categories: %s.", len(values), ", ".join(values.keys()))

    def find_binding(self, path: Union[str, Sequence[str]]) -> Maybe[InputBinding]:
        not_empty(path)

        segments: Sequence[str]

        if isinstance(path, str):
            segments = (path,)
        else:
            segments = path

        return self._resolve(segments, self).bind(lambda i: Some(i) if isinstance(i, InputBinding) else Nothing)

    def _resolve(self, path: Sequence[str], lookup: Any) -> Maybe[Any]:
        if not isinstance(lookup, Lookup):
            return Nothing

        return lookup.find(path[0]).bind(lambda i: Some(i) if len(path) == 1 else self._resolve(path[1:], i))

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

        return create_lookup(config, InputMap)
