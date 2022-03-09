from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Set

from bge.events import LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE
from bge.logic import KX_INPUT_ACTIVE, mouse
from returns.result import Result, ResultE
from rx import Observable, operators as ops

from alleycat.common import Point2D
from alleycat.core import BaseComponent
from alleycat.input import InputEvent
from alleycat.state import StateManager


class MouseButton(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2

    @property
    def event(self) -> int:
        if self == MouseButton.LEFT:
            return LEFTMOUSE
        elif self == MouseButton.MIDDLE:
            return MIDDLEMOUSE
        elif self == MouseButton.RIGHT:
            return RIGHTMOUSE
        else:
            assert False


@dataclass(frozen=True)
class MouseState:
    position: Point2D

    buttons: Set[MouseButton]

    __slots__ = ("position", "buttons")


class MouseInputSource(BaseComponent, StateManager[MouseState]):

    @property
    def init_state(self) -> ResultE[MouseState]:
        return Result.from_value(MouseState(Point2D(0.5, 0.5), set()))

    def next_state(self, state: MouseState) -> ResultE[MouseState]:
        i = mouse.activeInputs

        pos = Point2D.from_tuple(mouse.position)
        buttons = set(filter(lambda b: b.event in i and KX_INPUT_ACTIVE in i[b.event].status, MouseButton))

        return Result.from_value(MouseState(pos, buttons))

    @property
    def on_mouse_move(self) -> Observable[MouseMoveEvent]:
        return self.on_state_change.pipe(
            ops.map(partial(MouseMoveEvent, self)),
            ops.distinct_until_changed())

    @property
    def on_mouse_down(self) -> Observable[MouseButtonEvent]:
        return self.on_state_change.pipe(
            ops.map(lambda s: s.buttons),
            ops.distinct_until_changed(),
            ops.pairwise(),
            ops.flat_map(lambda b: b[1] - b[0]),
            ops.map(lambda b: MouseDownEvent(self, self.state.unwrap(), b)))

    @property
    def on_mouse_up(self) -> Observable[MouseButtonEvent]:
        return self.on_state_change.pipe(
            ops.map(lambda s: s.buttons),
            ops.distinct_until_changed(),
            ops.pairwise(),
            ops.flat_map(lambda b: b[0] - b[1]),
            ops.map(lambda b: MouseUpEvent(self, self.state.unwrap(), b)))


@dataclass(frozen=True)
class MouseEvent(InputEvent[MouseInputSource], ABC):
    state: MouseState

    @property
    def position(self) -> Point2D:
        return self.state.position

    @property
    def buttons(self) -> Set[MouseButton]:
        return self.state.buttons

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.state is None:
            raise ValueError("Argument 'state' is required.")


@dataclass(frozen=True)
class MouseButtonEvent(MouseEvent, ABC):
    button: MouseButton

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.button is None:
            raise ValueError("Argument 'button' is required.")


class MouseMoveEvent(MouseEvent):
    pass


class MouseDownEvent(MouseButtonEvent):
    pass


class MouseUpEvent(MouseButtonEvent):
    pass
