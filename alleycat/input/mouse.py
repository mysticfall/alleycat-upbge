from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Mapping, Set, Tuple

import bge
import rx
from alleycat.reactive import RP, RV, functions as rv
from rx import Observable, operators as ops
from rx.subject import Subject
from validator_collection import not_empty
from validator_collection.validators import json

from alleycat import log
from alleycat.common import ConfigMetaSchema
from alleycat.event import EventLoopAware, EventLoopScheduler
from alleycat.input import Axis2D, AxisInput, TriggerInput
from alleycat.log import LoggingSupport


class MouseButton(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2

    @property
    def event(self) -> int:
        if self == MouseButton.LEFT:
            return bge.events.LEFTMOUSE
        elif self == MouseButton.MIDDLE:
            return bge.events.MIDDLEMOUSE
        elif self == MouseButton.RIGHT:
            return bge.events.RIGHTMOUSE
        else:
            assert False


class MouseInputSource(EventLoopAware, LoggingSupport):
    position: RV[Tuple[float, float]] = rv.new_view()

    buttons: RV[Set[MouseButton]] = rv.new_view()

    show_pointer: RP[bool] = rv.from_value(False)

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        super().__init__(scheduler)

        self._position = Subject()
        self._activeInputs = Subject()

        # noinspection PyTypeChecker
        self.position = self._position.pipe(
            ops.start_with(bge.logic.mouse.position),
            ops.share())

        # noinspection PyTypeChecker
        self.buttons = self._activeInputs.pipe(
            ops.start_with({}),
            ops.map(lambda i: set(filter(
                lambda b: b.event in i and bge.logic.KX_INPUT_ACTIVE in i[b.event].status, MouseButton))),
            ops.share())

        rv.observe(self.show_pointer).subscribe(lambda v: bge.render.showMouse(v), on_error=self.error_handler)

    @property
    def on_input_change(self) -> Observable:
        return self._activeInputs

    def on_button_press(self, button: MouseButton) -> Observable:
        return rv.observe(self.buttons).pipe(
            ops.map(lambda b: button in b),
            ops.distinct_until_changed(),
            ops.pairwise(),
            ops.filter(lambda b: not b[0] and b[1]),
            ops.map(lambda _: button))

    def on_button_release(self, button: MouseButton) -> Observable:
        return rv.observe(self.buttons).pipe(
            ops.map(lambda b: button in b),
            ops.distinct_until_changed(),
            ops.pairwise(),
            ops.filter(lambda b: b[0] and not b[1]),
            ops.map(lambda _: button))

    def process(self) -> None:
        self._position.on_next(bge.logic.mouse.position)
        self._activeInputs.on_next(bge.logic.mouse.activeInputs)

        if not self.show_pointer:
            bge.logic.mouse.position = (0.5, 0.5)

    def dispose(self) -> None:
        super().dispose()

        self.execute_safely(self._position.dispose)
        self.execute_safely(self._activeInputs.dispose)


class MouseButtonInput(TriggerInput):

    def __init__(
            self,
            button: MouseButton,
            source: MouseInputSource,
            repeat: bool = False,
            enabled: bool = True) -> None:
        self._button = not_empty(button)
        self._source = not_empty(source)

        super().__init__(repeat=repeat, enabled=enabled)

    @property
    def button(self) -> MouseButton:
        return self._button

    @property
    def source(self) -> MouseInputSource:
        return self._source

    def create(self) -> Observable:
        if self.repeat:
            return rv.observe(self.source.buttons).pipe(ops.map(lambda b: self.button in b))
        else:
            pressed = self.source.on_button_press(self.button).pipe(ops.map(lambda _: True))
            released = self.source.on_button_release(self.button).pipe(ops.map(lambda _: False))

            return rx.merge(pressed, released)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "mouse_button"},
                "button": {
                    "oneOf": [
                        {"const": "LEFT"},
                        {"const": "MIDDLE"},
                        {"const": "RIGHT"}
                    ]
                },
                "enabled": {"type": "boolean"},
                "repeat": {"type": "boolean"}
            },
            "required": ["type", "button"]
        }

    @classmethod
    def from_config(cls, source: MouseInputSource, config: Mapping[str, Any]) -> MouseButtonInput:
        not_empty(source)
        not_empty(config)

        logger = logging.getLogger(cls.__name__)

        logger.debug("Creating a key press input from config: %s", config)

        json(config, cls.config_schema())

        enabled = "enabled" not in config or config["enabled"]
        repeat = "repeat" in config and config["repeat"]
        button = getattr(MouseButton, config["button"])

        return MouseButtonInput(button, source, repeat, enabled)


class MouseAxisInput(AxisInput):

    def __init__(
            self,
            axis: Axis2D,
            source: MouseInputSource,
            window_size: float = 0,
            window_shift: float = 0,
            sensitivity: float = 1.0,
            dead_zone: float = 0.0,
            enabled: bool = True) -> None:
        self._axis = not_empty(axis)
        self._source = not_empty(source)

        super().__init__(
            window_size=window_size,
            window_shift=window_shift,
            sensitivity=sensitivity,
            dead_zone=dead_zone,
            enabled=enabled)

        self.logger.debug("Binding to axis '%s'.", axis.name)

    @property
    def axis(self) -> Axis2D:
        return self._axis

    @property
    def source(self) -> MouseInputSource:
        return self._source

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self.source.scheduler

    def create(self) -> Observable:
        return rv.observe(self.source.position).pipe(
            ops.filter(lambda _: not self.source.show_pointer),
            ops.map(lambda v: (v[self.axis.value] - 0.5) * 2.0))

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "mouse_axis"},
                "axis": {
                    "oneOf": [
                        {"const": "x"},
                        {"const": "y"}
                    ]
                },
                "window_size": {"type": "number", "minimum": 0, "maximum": 1},
                "window_shift": {"type": "number", "minimum": 0, "maximum": 1},
                "sensitivity": {"type": "number", "minimum": 0},
                "dead_zone": {"type": "number", "minimum": 0, "maximum": 1},
                "enabled": {"type": "boolean"}
            },
            "required": ["type", "axis"]
        }

    @classmethod
    def from_config(cls, source: MouseInputSource, config: Mapping[str, Any]) -> MouseAxisInput:
        not_empty(source)
        not_empty(config)

        logger = log.get_logger(cls)

        logger.debug("Creating a mouse axis input from config: %s", config)

        json(config, cls.config_schema())

        enabled = "enabled" not in config or config["enabled"]

        axis = getattr(Axis2D, str(config["axis"]).upper())

        window_size = config.get("window_size", 0)
        window_shift = config.get("window_shift", 0)

        sensitivity = config.get("sensitivity", 1.0)
        dead_zone = config.get("dead_zone", 0.0)

        return MouseAxisInput(axis, source, window_size, window_shift, sensitivity, dead_zone, enabled)


class MouseWheelInput(AxisInput):

    def __init__(
            self,
            source: MouseInputSource,
            window_size: float = 0.1,
            window_shift: float = 0.01,
            sensitivity: float = 1.0,
            dead_zone: float = 0.0,
            enabled: bool = True) -> None:
        self._source = not_empty(source)

        super().__init__(
            window_size=window_size,
            window_shift=window_shift,
            sensitivity=sensitivity,
            dead_zone=dead_zone,
            enabled=enabled)

        self.logger.debug("Initialising mouse wheel input(sensitivity=%f, dead_zone=%f).", sensitivity, dead_zone)

    @property
    def source(self) -> MouseInputSource:
        return self._source

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self.source.scheduler

    def create(self) -> Observable:
        def get_value(events):
            if bge.events.WHEELUPMOUSE in events:
                return events[bge.events.WHEELUPMOUSE].values[-1]
            if bge.events.WHEELDOWNMOUSE in events:
                return events[bge.events.WHEELDOWNMOUSE].values[-1]

            return 0

        return self.source.on_input_change.pipe(ops.map(get_value))

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "mouse_wheel"},
                "window_size": {"type": "number", "minimum": 0, "maximum": 1},
                "window_shift": {"type": "number", "minimum": 0, "maximum": 1},
                "sensitivity": {"type": "number", "minimum": 0},
                "dead_zone": {"type": "number", "minimum": 0, "maximum": 1},
                "enabled": {"type": "boolean"}
            },
            "required": ["type"]
        }

    @classmethod
    def from_config(cls, source: MouseInputSource, config: Mapping[str, Any]) -> MouseWheelInput:
        not_empty(source)
        not_empty(config)

        logger = log.get_logger(cls)

        logger.debug("Creating a mouse axis input from config: %s", config)

        json(config, cls.config_schema())

        enabled = "enabled" not in config or config["enabled"]

        window_size = config.get("window_size", 0.1)
        window_shift = config.get("window_shift", 0.01)

        sensitivity = config.get("sensitivity", 1.0)
        dead_zone = config.get("dead_zone", 0.0)

        return MouseWheelInput(
            source,
            window_size=window_size,
            window_shift=window_shift,
            sensitivity=sensitivity,
            dead_zone=dead_zone,
            enabled=enabled)
