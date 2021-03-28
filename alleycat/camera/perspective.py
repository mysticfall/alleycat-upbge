from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from returns.converters import maybe_to_result
from returns.iterables import Fold
from returns.result import ResultE, Success

from alleycat.camera import CameraControl
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.control import TurretControl


class PerspectiveCamera(TurretControl[KX_Camera], CameraControl, ABC):
    class ArgKeys(ActivatableComponent.ArgKeys):
        PIVOT: Final = "Pivot"
        VIEWPOINT: Final = "Viewpoint"

    args = OrderedDict(chain(TurretControl.args.items(), (
        (ArgKeys.PIVOT, Object),
        (ArgKeys.VIEWPOINT, Object)
    )))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    @property
    def pivot(self) -> KX_GameObject:
        return self.parameters["pivot"]

    @property
    def viewpoint(self) -> KX_GameObject:
        return self.parameters["viewpoint"]

    def validate(self, args: ArgumentReader) -> ResultE[Mapping]:
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

        inherited = super().validate(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
