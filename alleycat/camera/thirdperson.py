from collections import OrderedDict

import bge
from bge.types import KX_GameObject, KX_Scene
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane

from alleycat.camera import CameraControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class ThirdPersonCamera(CameraControl):
    args = OrderedDict((
        ("Pivot", Object),
        ("Viewpoint", Object),
    ))

    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

    @inject
    def start(self, args: dict, input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        super().start(args)

        scene: KX_Scene = bge.logic.getCurrentScene()

        self.pivot: KX_GameObject = scene.getGameObjectFromObject(args["Pivot"])
        self.viewpoint: KX_GameObject = scene.getGameObjectFromObject(args["Viewpoint"])

        self.logger.info("Input map: %s", input_map)
        self.logger.info("Pivot object: %s", self.pivot)

        self.distance = 1.0

    def update(self) -> None:
        up_axis = self.pivot.worldOrientation @ Vector((0, 0, 1))

        height = distance_point_to_plane(self.viewpoint.worldPosition, self.pivot.worldPosition, up_axis)

        mat = self.rotation.to_matrix()

        orientation = self.pivot.worldOrientation @ mat @ self.base_rotation
        offset = self.pivot.worldOrientation @ mat @ Vector((0, -1, 0)) * self.distance

        self.object.worldOrientation = orientation
        self.object.worldPosition = self.pivot.worldPosition - offset + up_axis * height * 0.8
