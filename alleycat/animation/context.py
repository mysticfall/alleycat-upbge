from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from bpy.types import Action
from returns.maybe import Maybe
from validator_collection import validators


class PlayMode(Enum):
    """bge.logic.KX_ACTION_MODE_PLAY"""
    Play = 0

    """bge.logic.KX_ACTION_MODE_LOOP"""
    Loop = 1

    """bge.logic.KX_ACTION_MODE_PING_PONG"""
    PingPong = 2


class BlendMode(Enum):
    """bge.logic.KX_ACTION_BLEND_BLEND"""
    Blend = 0

    """bge.logic.KX_ACTION_BLEND_ADD"""
    Add = 1


class AnimationContext(ABC):
    __slots__ = ["_time_delta", "_layer", "_weight", "_speed"]

    def __init__(self, time_delta: float = 0, layer: int = 10000) -> None:
        self._time_delta = validators.float(time_delta, minimum=0.0)
        self._layer = validators.integer(layer, minimum=0)
        self._weight = 1.0
        self._speed = 1.0

    @property
    def time_delta(self) -> float:
        return self._time_delta

    @property
    def layer(self) -> int:
        return self._layer

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def speed(self) -> float:
        return self._speed

    @abstractmethod
    def play(self,
             action: Action,
             start_frame: Optional[float] = None,
             end_frame: Optional[float] = None,
             priority=0,
             blend: float = 0,
             play_mode: PlayMode = PlayMode.Play,
             blend_mode: BlendMode = BlendMode.Blend) -> None:
        pass

    @abstractmethod
    def stop(self):
        pass

    @property
    @abstractmethod
    def action(self) -> Maybe[Action]:
        pass

    @property
    @abstractmethod
    def frame(self) -> float:
        pass

    @frame.setter
    @abstractmethod
    def frame(self, value: float) -> None:
        pass

    @property
    @abstractmethod
    def playing(self) -> bool:
        pass
