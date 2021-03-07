from bge.types import KX_Camera, KX_GameObject

from alleycat.camera import PerspectiveCamera


class FirstPersonCamera(PerspectiveCamera):

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj=obj)

    def process(self, pivot: KX_GameObject, viewpoint: KX_GameObject) -> None:
        assert pivot
        assert viewpoint

        rotation = self.rotation.to_matrix()

        # noinspection PyUnresolvedReferences
        orientation = pivot.worldOrientation @ rotation @ self.base_rotation

        self.object.worldOrientation = orientation
        self.object.worldPosition = viewpoint.worldPosition
