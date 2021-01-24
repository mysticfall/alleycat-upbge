from __future__ import annotations

import logging
from abc import ABC
from enum import Enum
from itertools import chain
from typing import Any, Callable, Mapping, Optional, Sequence

from dependency_injector import providers
from rx import Observable, operators as ops
from validator_collection import validators
from validator_collection.validators import json, not_empty, numeric

from alleycat.input import Input, InputBinding


class Axis2D(Enum):
    X = 0
    Y = 1


class AxisInput(Input[float], ABC):

    def __init__(
            self,
            init_value: float = 0.0,
            sensitivity: float = 1.0,
            dead_zone: float = 0.0,
            enabled: bool = True) -> None:
        self._dead_zone = numeric(dead_zone, minimum=0, maximum=1)
        self._sensitivity = numeric(sensitivity, minimum=0)

        super().__init__(init_value=validators.float(init_value), enabled=enabled)

    @property
    def dead_zone(self) -> float:
        return self._dead_zone

    @dead_zone.setter
    def dead_zone(self, value: float) -> None:
        self._dead_zone = numeric(value, minimum=0)

    @property
    def sensitivity(self) -> float:
        return self._sensitivity

    @sensitivity.setter
    def sensitivity(self, value: float) -> None:
        self._sensitivity = numeric(value, minimum=0)

    @property
    def modifiers(self) -> Sequence[Callable[[Observable], Observable]]:
        return tuple(chain(super().modifiers, (
            ops.map(lambda v: v * self.sensitivity),
            ops.map(lambda v: v if abs(v) >= self.dead_zone else 0),
            ops.map(lambda v: min(max(v, -1), 1)))))


class AxisBinding(InputBinding[AxisInput]):

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        super().__init__(name, description)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "description": {"type": "string"},
                "input": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "object"},
                        "y": {"type": "object"}
                    }
                }
            },
            "required": ["name", "type"]
        }

    @classmethod
    def from_config(cls, input_factory: providers.Provider[Input], config: Mapping[str, Any]) -> AxisBinding:
        not_empty(input_factory)

        logger = logging.getLogger(AxisBinding.__name__)
        logger.info(config)

        json(config, cls.config_schema())

        name = config["name"]
        description = config["description"] if "description" in config else None

        if "input" in config:
            input_conf = config["input"]

            if "x" in input_conf and "type" in input_conf["x"]["type"]:
                x = input_factory(input_conf["x"]["type"], input_conf["x"])

            if "y" in input_conf:
                y = input_factory(input_conf["y"]["type"], input_conf["y"])

        return AxisBinding(name, description)
