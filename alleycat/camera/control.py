import math
from math import radians

from alleycat.reactive import RP, RV, ReactiveObject, functions as rv
from bge.types import KX_GameObject, KX_PythonComponent
from dependency_injector.wiring import Provide, inject
from mathutils import Euler, Matrix, Vector
from rx import operators as ops

from alleycat.game import GameContext
from alleycat.input import InputMap
from alleycat.log import LoggingSupport


class CameraControl(LoggingSupport, ReactiveObject, KX_PythonComponent):
    pitch: RP[float] = rv.from_value(0.0).map(lambda _, v: min(max(v, -math.pi), math.pi))

    yaw: RP[float] = rv.from_value(0.0).map(lambda _, v: min(max(v, -math.pi), math.pi))

    rotation: RV[Euler] = rv.combine_latest(pitch, yaw)(ops.map(lambda v: Euler((v[0], 0, -v[1]), "XYZ")))

    # noinspection PyUnresolvedReferences
    base_rotation: Matrix = Matrix.Rotation(radians(180), 3, "Z") @ Matrix.Rotation(radians(90), 3, "X")

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        def rotate(value: Vector):
            self.pitch += value.y
            self.yaw += value.x

        rotate_input = input_map["view"]["rotate"]

        rv.observe(rotate_input.value).subscribe(rotate, on_error=self.error_handler)
