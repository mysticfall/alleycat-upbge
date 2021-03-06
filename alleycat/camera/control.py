from abc import ABC
from math import radians

from bge.types import KX_Camera
from bpy.types import Camera
from mathutils import Matrix

from alleycat.common import IDComponent


class CameraControl(IDComponent[KX_Camera, Camera], ABC):
    # noinspection PyUnresolvedReferences
    _base_rotation: Matrix = Matrix.Rotation(radians(180), 3, "Z") @ Matrix.Rotation(radians(90), 3, "X")

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    @property
    def base_rotation(self) -> Matrix:
        return self._base_rotation
