import math
from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from alleycat.reactive import RP, RV, functions as rv
from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from mathutils import Euler
from returns.converters import maybe_to_result
from returns.iterables import Fold
from returns.result import ResultE, Success
from rx import operators as ops

from alleycat.camera import CameraControl
from alleycat.common import ActivatableComponent, ArgumentReader, clamp, normalize_angle


class RotatableCamera(CameraControl, ABC):
    class ArgKeys(ActivatableComponent.ArgKeys):
        PIVOT: Final = "Pivot"
        VIEWPOINT: Final = "Viewpoint"

    args = OrderedDict(chain(CameraControl.args.items(), (
        (ArgKeys.PIVOT, Object),
        (ArgKeys.VIEWPOINT, Object)
    )))

    pitch: RP[float] = rv.from_value(0.0).validate(lambda _, v: clamp(v, -math.pi / 2, math.pi / 2))

    yaw: RP[float] = rv.from_value(0.0).validate(lambda _, v: normalize_angle(v))

    # noinspection PyArgumentList
    rotation: RV[Euler] = rv.combine_latest(pitch, yaw)(ops.map(lambda v: Euler((v[0], 0, -v[1]), "XYZ")))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    @property
    def pivot(self) -> KX_GameObject:
        return self.params["pivot"]

    @property
    def viewpoint(self) -> KX_GameObject:
        return self.params["viewpoint"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        pivot = args \
            .require(self.ArgKeys.PIVOT, Object) \
            .map(self.as_game_object) \
            .alt(lambda _: ValueError("Missing or invalid pivot object."))

        viewpoint = maybe_to_result(
            args.read(self.ArgKeys.VIEWPOINT, Object).map(self.as_game_object)).lash(lambda _: pivot)

        result = Fold.collect((
            pivot.map(lambda p: ("pivot", p)),
            viewpoint.map(lambda v: ("viewpoint", v))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
