from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from alleycat.reactive import RP, functions as rv
from bge.types import KX_Camera
from returns.iterables import Fold
from returns.result import ResultE, Success

from alleycat.camera import CameraControl
from alleycat.common import ArgumentReader


class ZoomableCamera(CameraControl, ABC):
    class ArgKeys(CameraControl.ArgKeys):
        MIN_DISTANCE: Final = "Minimum Distance"

    args = OrderedDict(chain(CameraControl.args.items(), (
        (ArgKeys.MIN_DISTANCE, 0.3),
    )))

    distance: RP[float] = rv.from_value(1.0).map(lambda c, v: max(v, c.min_distance))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    @property
    def min_distance(self) -> float:
        return self.params["min_distance"] if self.initialized else 0

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        min_distance = args.read(ZoomableCamera.ArgKeys.MIN_DISTANCE, float).value_or(0.3)

        result = Fold.collect((
            Success(("min_distance", min_distance)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
