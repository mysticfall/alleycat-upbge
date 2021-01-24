from __future__ import annotations

import logging
from abc import ABC
from typing import Any, Mapping, Optional

from dependency_injector import providers
from validator_collection import not_empty
from validator_collection.validators import json

from alleycat.common import ConfigMetaSchema
from alleycat.input import Input, InputBinding


class TriggerInput(Input[bool], ABC):

    def __init__(self, enabled: bool = True) -> None:
        super().__init__(init_value=False, enabled=enabled)


class TriggerBinding(InputBinding):

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        super().__init__(name, description)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"const": "trigger"},
                "description": {"type": "string"}
            },
            "required": ["name", "type"]
        }

    @classmethod
    def from_config(cls, input_factory: providers.Provider[Input], config: Mapping[str, Any]) -> TriggerBinding:
        not_empty(input_factory)

        logger = logging.getLogger(cls.__name__)

        logger.debug("Creating a trigger binding from config: %s", config)

        json(config, cls.config_schema())

        name = config["name"]
        description = config["description"] if "description" in config else None

        return TriggerBinding(name, description)
