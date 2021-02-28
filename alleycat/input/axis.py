from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from itertools import chain
from typing import Any, Callable, Mapping, Optional, Sequence

import mathutils
import rx
from alleycat.reactive import RP, RV, functions as rv
from dependency_injector import providers
from mathutils import Vector
from returns.iterables import Fold
from returns.maybe import Maybe, Some
from rx import Observable, operators as ops
from validator_collection import validators
from validator_collection.validators import json, not_empty, numeric

from alleycat import log
from alleycat.common import ConfigMetaSchema
from alleycat.event import EventLoopScheduler
from alleycat.input import Input, InputBinding


class Axis2D(Enum):
    X = 0
    Y = 1


class AxisInput(Input[float], ABC):

    def __init__(
            self,
            init_value: float = 0.0,
            window_size: float = 0,
            window_shift: float = 0,
            sensitivity: float = 1.0,
            dead_zone: float = 0.0,
            enabled: bool = True) -> None:
        self._window_size = numeric(window_size, minimum=0, maximum=1)
        self._window_shift = numeric(window_shift, minimum=0, maximum=1)
        self._sensitivity = numeric(sensitivity, minimum=0)
        self._dead_zone = numeric(dead_zone, minimum=0, maximum=1)

        self.logger.debug("Axis parameters: sensitivity=%f, dead_zone=%f.", sensitivity, dead_zone)
        self.logger.debug("Smoothing parameters: window_size=%f, window_shift=%f.", window_size, window_shift)

        super().__init__(init_value=validators.float(init_value), enabled=enabled)

    @property
    def window_size(self) -> float:
        return self._window_size

    @property
    def window_shift(self) -> float:
        return self._window_shift

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
    @abstractmethod
    def scheduler(self) -> EventLoopScheduler:
        pass

    @property
    def modifiers(self) -> Sequence[Callable[[Observable], Observable]]:
        axis_modifiers = (ops.map(lambda v: v * self.sensitivity),
                          ops.map(lambda v: v if abs(v) >= self.dead_zone else 0),
                          ops.map(lambda v: min(max(v, -1), 1)))

        if self.window_size > 0:
            smoothing = (ops.buffer_with_time(self.window_size, self.window_shift, self.scheduler),
                         ops.filter(lambda v: len(v) > 0),
                         ops.map(lambda v: sum(v) / len(v)))

            return tuple(chain(super().modifiers, axis_modifiers, smoothing))

        return tuple(chain(super().modifiers, axis_modifiers))


class AxisBinding(InputBinding[float]):
    input: RP[Maybe[AxisInput]] = rv.new_property().pipe(
        lambda b: (ops.do_action(lambda i: b.logger.debug("Set axis input to %s.", i)),))

    # noinspection PyTypeChecker,PyShadowingBuiltins
    value: RV[float] = input.as_view().pipe(lambda b: (
        ops.map(lambda i: i.map(lambda v: v.observe("value")).value_or(rx.return_value(0))),
        ops.switch_latest(),
        ops.start_with(0),
        ops.do_action(b.log_value),))

    # noinspection PyShadowingBuiltins
    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            input: Optional[AxisInput] = None) -> None:

        super().__init__(name, description)

        # noinspection PyTypeChecker
        self.input = Maybe.from_optional(input)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "axis"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "input": {
                    "type": "object"
                }
            },
            "required": ["name", "type"]
        }

    @classmethod
    def from_config(cls, input_factory: providers.Provider[Input], config: Mapping[str, Any]) -> AxisBinding:
        not_empty(input_factory)

        logger = log.get_logger(cls)

        logger.debug("Creating an axis binding from config: %s.", config)

        json(config, cls.config_schema())

        name = config["name"]
        description = config["description"] if "description" in config else None

        if "input" in config:
            input_conf = config["input"]

            def bind_input() -> Optional[AxisInput]:
                if "type" in input_conf:
                    # noinspection PyShadowingBuiltins,PyTypeChecker
                    return input_factory(input_conf["type"], input_conf)
                else:
                    return None

            return AxisBinding(name, description, input=bind_input())

        return AxisBinding(name, description)


class Axis2DBinding(InputBinding[Vector]):
    x_input: RP[Maybe[AxisInput]] = rv.new_property().pipe(
        lambda b: (ops.do_action(lambda i: b.logger.debug("Set X axis input to %s.", i)),))

    y_input: RP[Maybe[AxisInput]] = rv.new_property().pipe(
        lambda b: (ops.do_action(lambda i: b.logger.debug("Set Y axis input to %s.", i)),))

    # noinspection PyTypeChecker
    value: RV[Vector] = rv.combine_latest(x_input, y_input)(ops.pipe(
        ops.map(lambda v: Fold.collect_all(v, Some(()))),
        ops.map(lambda v: v.map(lambda a:
                                rx.combine_latest(a[0].observe("value"), a[1].observe("value")) if len(a) == 2
                                else rx.return_value((0.0, 0.0)))),
        ops.map(lambda v: v.value_or(rx.return_value((0.0, 0.0)))),
        ops.switch_latest(),
        ops.map(lambda v: mathutils.Vector(v)))  # To allow test mockup. I know it's ugly but do we have any better way?
    ).pipe(lambda b: (ops.do_action(b.log_value),))

    def __init__(
            self, name: str,
            description: Optional[str] = None,
            x_input: Optional[AxisInput] = None,
            y_input: Optional[AxisInput] = None) -> None:

        super().__init__(name, description)

        # noinspection PyTypeChecker
        self.x_input = Maybe.from_optional(x_input)

        # noinspection PyTypeChecker
        self.y_input = Maybe.from_optional(y_input)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "axis2d"},
                "name": {"type": "string"},
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
    def from_config(cls, input_factory: providers.Provider[Input], config: Mapping[str, Any]) -> Axis2DBinding:
        not_empty(input_factory)

        logger = log.get_logger(cls)

        logger.debug("Creating a 2D axis binding from config: %s.", config)

        json(config, cls.config_schema())

        name = config["name"]
        description = config["description"] if "description" in config else None

        if "input" in config:
            input_conf = config["input"]

            def bind_input(axis: str) -> Optional[AxisInput]:
                if axis in input_conf and "type" in input_conf[axis]:
                    # noinspection PyShadowingBuiltins,PyTypeChecker
                    return input_factory(input_conf[axis]["type"], input_conf[axis])
                else:
                    return None

            return Axis2DBinding(name, description, x_input=bind_input("x"), y_input=bind_input("y"))

        return Axis2DBinding(name, description)
