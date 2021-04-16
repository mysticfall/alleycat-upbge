from abc import ABC

from alleycat.reactive import RP, functions as rv
from bge.types import KX_Camera

from alleycat.camera import CameraControl


class ZoomableCamera(CameraControl, ABC):
    distance: RP[float] = rv.from_value(1.0).map(lambda _, v: max(v, 0.0))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)
