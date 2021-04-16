from abc import ABC

from bge.types import KX_Camera

from alleycat.camera import RotatableCamera


class PerspectiveCamera(RotatableCamera, ABC):

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)
