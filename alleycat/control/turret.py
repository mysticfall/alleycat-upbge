import math
from abc import ABC
from typing import Generic, TypeVar

from alleycat.reactive import RP, RV, functions as rv
from bge.types import KX_GameObject
from mathutils import Euler
from rx import operators as ops

from alleycat.common import ActivatableComponent, clamp, normalize_angle

T = TypeVar("T", bound=KX_GameObject)


class TurretControl(Generic[T], ActivatableComponent[T], ABC):

    pitch: RP[float] = rv.from_value(0.0).validate(lambda _, v: clamp(v, -math.pi / 2, math.pi / 2))

    yaw: RP[float] = rv.from_value(0.0).validate(lambda _, v: normalize_angle(v))

    # noinspection PyArgumentList
    rotation: RV[Euler] = rv.combine_latest(pitch, yaw)(ops.map(lambda v: Euler((v[0], 0, -v[1]), "XYZ")))

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
