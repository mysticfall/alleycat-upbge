from __future__ import annotations

import logging
from enum import IntFlag
from functools import reduce
from typing import Any, Mapping, Tuple

import bge
import rx
from alleycat.reactive import RP, RV, functions as rv
from bge.types import SCA_InputEvent
from rx import Observable, operators as ops
from rx.subject import Subject
from validator_collection import not_empty
from validator_collection.validators import json

from alleycat.common import ConfigMetaSchema
from alleycat.event import EventLoopAware, EventLoopScheduler
from alleycat.input import Axis2D, AxisInput, TriggerInput
from alleycat.log import LoggingSupport


class MouseButton(IntFlag):
    LEFT = 1
    MIDDLE = 2
    RIGHT = 4

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

    buttons: RV[int] = rv.new_view()

    show_pointer: RP[bool] = rv.from_value(False)

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        super().__init__(scheduler)

        self._position = Subject()
        self._activeInputs = Subject()

        # noinspection PyTypeChecker
        self.position = self._position.pipe(
            ops.start_with(bge.logic.mouse.position),
            ops.distinct_until_changed(),
            ops.share())

        def pressed(e: SCA_InputEvent) -> bool:
            return bge.logic.KX_INPUT_ACTIVE in e.status or bge.logic.KX_INPUT_JUST_ACTIVATED in e.status

        # noinspection PyTypeChecker
        self.buttons = self._activeInputs.pipe(
            ops.start_with({}),
            ops.map(lambda i: map(lambda b: b if b.event in i and pressed(i[b.event]) else 0, MouseButton)),
            ops.map(lambda v: reduce(lambda a, b: a | b, v)),
            ops.distinct_until_changed(),
            ops.share())

        self.observe("show_pointer").subscribe(lambda v: bge.render.showMouse(v), on_error=self.error_handler)

    @property
    def on_wheel_move(self) -> Observable:
        def on_wheel(code: int) -> Observable:
            return self._activeInputs.pipe(
                ops.filter(lambda i: code in i),
                ops.map(lambda i: i[code].values[-1]),
                ops.filter(lambda v: v != 0))

        return rx.merge(on_wheel(bge.events.WHEELUPMOUSE), on_wheel(bge.events.WHEELDOWNMOUSE))

    def on_button_press(self, button: MouseButton) -> Observable:
        return self.observe("buttons").pipe(ops.filter(lambda b: b & button == button))

    def on_button_release(self, button: MouseButton) -> Observable:
        return self.observe("buttons").pipe(
            ops.map(lambda b: b & button),
            ops.distinct_until_changed(),
            ops.pairwise(),
            ops.filter(lambda b: b[0] == button and b[1] != button),
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

    def __init__(self, button: MouseButton, source: MouseInputSource, enabled: bool = True) -> None:
        self._button = not_empty(button)
        self._source = not_empty(source)

        super().__init__(enabled=enabled)

    @property
    def button(self) -> MouseButton:
        return self._button

    @property
    def source(self) -> MouseInputSource:
        return self._source

    def create(self) -> Observable:
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
                "enabled": {"type": "boolean"}
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
        button = getattr(MouseButton, config["button"])

        return MouseButtonInput(button, source, enabled)


class MouseAxisInput(AxisInput):

    def __init__(
            self,
            axis: Axis2D,
            source: MouseInputSource,
            sensitivity: float = 1.0,
            dead_zone: float = 0.0,
            enabled: bool = True) -> None:
        self._axis = not_empty(axis)
        self._source = not_empty(source)

        super().__init__(sensitivity=sensitivity, dead_zone=dead_zone, enabled=enabled)

    @property
    def axis(self) -> Axis2D:
        return self._axis

    @property
    def source(self) -> MouseInputSource:
        return self._source

    def create(self) -> Observable:
        return self.source.observe("position").pipe(
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

        logger = logging.getLogger(cls.__name__)

        logger.debug("Creating a key press input from config: %s", config)

        json(config, cls.config_schema())

        enabled = "enabled" not in config or config["enabled"]
        axis = getattr(Axis2D, str(config["axis"]).upper())
        sensitivity = config.get("sensitivity", 1.0)
        dead_zone = config.get("dead_zone", 0.0)

        return MouseAxisInput(axis, source, sensitivity, dead_zone, enabled)
