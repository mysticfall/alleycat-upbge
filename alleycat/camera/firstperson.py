from bge.types import KX_Camera

from alleycat.camera import PerspectiveCamera


class FirstPersonCamera(PerspectiveCamera):

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj)

    def initialize(self) -> None:
        def process():
            rotation = self.rotation.to_matrix()

            # noinspection PyUnresolvedReferences
            orientation = self.pivot.worldOrientation @ rotation @ self.base_rotation

            self.object.worldOrientation = orientation
            self.object.worldPosition = self.viewpoint.worldPosition

        self.on_update.subscribe(lambda _: process(), on_error=self.error_handler)

        super().initialize()
