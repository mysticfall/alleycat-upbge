from __future__ import annotations

from abc import ABC
from typing import Any, Mapping, Optional

import rx
from alleycat.reactive import RP, RV, functions as rv
from dependency_injector import providers
from returns.maybe import Maybe
from rx import operators as ops
from validator_collection import not_empty
from validator_collection.validators import json

from alleycat import log
from alleycat.common import ConfigMetaSchema
from alleycat.input import Input, InputBinding


class TriggerInput(Input[bool], ABC):

    def __init__(self, repeat: bool = False, enabled: bool = True) -> None:
        super().__init__(init_value=False, repeat=repeat, enabled=enabled)


class TriggerBinding(InputBinding[bool]):
    input: RP[Maybe[TriggerInput]] = rv.new_property().pipe(
        lambda b: (ops.do_action(lambda i: b.logger.debug("Set trigger input to %s.", i)),))

    # noinspection PyTypeChecker,PyShadowingBuiltins
    value: RV[bool] = input.as_view().pipe(lambda b: (
        ops.map(lambda i: i.map(lambda v: v.observe("value")).value_or(rx.return_value(0))),
        ops.switch_latest(),
        ops.start_with(False),
        ops.do_action(b.log_value),))

    # noinspection PyShadowingBuiltins
    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            input: Optional[TriggerInput] = None) -> None:
        super().__init__(name, description)

        # noinspection PyTypeChecker
        self.input = Maybe.from_optional(input)

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

        logger = log.get_logger(cls)

        logger.debug("Creating a trigger binding from config: %s", config)

        json(config, cls.config_schema())

        name = config["name"]
        description = config["description"] if "description" in config else None

        if "input" in config:
            input_conf = config["input"]

            def bind_input() -> Optional[TriggerInput]:
                if "type" in input_conf:
                    # noinspection PyShadowingBuiltins,PyTypeChecker
                    return input_factory(input_conf["type"], input_conf)
                else:
                    return None

            return TriggerBinding(name, description, input=bind_input())

        return TriggerBinding(name, description)
