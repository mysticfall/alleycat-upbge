from __future__ import annotations

import logging
from enum import Enum
from itertools import chain
from typing import Any, Mapping, Set

import bge
import rx
from alleycat.reactive import RV, functions as rv
from rx import Observable, operators as ops
from rx.subject import Subject
from validator_collection import is_string
from validator_collection.validators import json, not_empty

from alleycat.common import ConfigMetaSchema
from alleycat.event import EventLoopAware, EventLoopScheduler
from alleycat.input import TriggerInput
from alleycat.log import LoggingSupport


class KeyState(Enum):
    Released = 0
    Pressed = 1
    Hold = 2


class KeyInputSource(EventLoopAware, LoggingSupport):
    pressed: RV[Set[int]] = rv.new_view()

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        super().__init__(scheduler)

        self._activeInputs = Subject()

        # noinspection PyTypeChecker
        self.pressed = self._activeInputs.pipe(
            ops.start_with({}),
            ops.map(lambda s: set(s.keys())))

        def to_state(previous: Set[int], current: Set[int]) -> Mapping[int, KeyState]:
            hold = map(lambda k: (k, KeyState.Hold), current.intersection(previous))
            pressed = map(lambda k: (k, KeyState.Pressed), current.difference(previous))
            released = map(lambda k: (k, KeyState.Released), previous.difference(current))

            return dict(chain(hold, pressed, released))

        self._states = self.observe("pressed").pipe(
            ops.start_with(set()),
            ops.pairwise(),
            ops.map(lambda s: to_state(s[0], s[1])),
            ops.share())

    def on_key_state_change(self, key_code: int) -> Observable:
        return self._states.pipe(ops.filter(lambda s: key_code in s), ops.map(lambda s: s[key_code]))

    def on_key_press(self, key_code: int) -> Observable:
        return self.on_key_state_change(key_code).pipe(
            ops.filter(lambda s: s == KeyState.Pressed),
            ops.map(lambda _: key_code))

    def on_key_release(self, key_code: int) -> Observable:
        return self.on_key_state_change(key_code).pipe(
            ops.filter(lambda s: s == KeyState.Released),
            ops.map(lambda _: key_code))

    def process(self) -> None:
        self._activeInputs.on_next(bge.logic.keyboard.activeInputs)

    def dispose(self) -> None:
        super().dispose()

        self.execute_safely(self._activeInputs.dispose)


class KeyPressInput(TriggerInput):

    def __init__(self, keycode: int, source: KeyInputSource, repeat: bool = False, enabled: bool = True) -> None:
        bge.events.EventToString(keycode)

        self._keycode = keycode
        self._source = not_empty(source)

        super().__init__(repeat=repeat, enabled=enabled)

    @property
    def keycode(self) -> int:
        return self._keycode

    @property
    def source(self) -> KeyInputSource:
        return self._source

    def create(self) -> Observable:
        if self.repeat:
            return self.source.observe("pressed").pipe(ops.map(lambda p: self.keycode in p))
        else:
            pressed = self.source.on_key_press(self.keycode).pipe(ops.map(lambda _: True))
            released = self.source.on_key_release(self.keycode).pipe(ops.map(lambda _: False))

            return rx.merge(pressed, released)

    @classmethod
    def config_schema(cls) -> object:
        return {
            "$schema": ConfigMetaSchema,
            "type": "object",
            "properties": {
                "type": {"const": "key_press"},
                "key": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "number"}
                    ]
                },
                "repeat": {"type": "boolean"},
                "enabled": {"type": "boolean"}
            },
            "required": ["type", "key"]
        }

    @classmethod
    def from_config(cls, source: KeyInputSource, config: Mapping[str, Any]) -> KeyPressInput:
        not_empty(source)
        not_empty(config)

        logger = logging.getLogger(cls.__name__)

        logger.debug("Creating a key press input from config: \n %s", config)

        json(config, cls.config_schema())

        key = config["key"]

        if is_string(key):
            key = getattr(bge.events, key)

        enabled = "enabled" not in config or config["enabled"]
        repeat = "repeat" in config and config["repeat"]

        return KeyPressInput(key, source, repeat, enabled)
