from collections import OrderedDict
from math import radians

import bge
from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent, KX_Scene
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from numpy import sign

from alleycat.camera import CameraControl
from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.input import InputMap
from alleycat.log import LoggingSupport


class Character(LoggingSupport, ReactiveObject, KX_PythonComponent):
    args = OrderedDict((
        ("name", "Player"),
        ("camera", Object),
    ))

    _last_pos: Vector

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings],
            scheduler: EventLoopScheduler = Provide[GameContext.scheduler]) -> None:
        self.name = args["name"]

        scene: KX_Scene = bge.logic.getCurrentScene()
        camera: KX_GameObject = scene.getGameObjectFromObject(args["camera"])

        view: CameraControl = None

        for comp in camera.components:
            if isinstance(comp, CameraControl):
                self.view = comp
                break

        self._last_pos = self.object.worldPosition.copy()

        self.logger.info("Input map: %s", input_map)
        self.logger.info("Camera: %s", view)

    def update(self) -> None:
        pos = self.object.worldPosition.copy()

        if (pos - self._last_pos).length_squared > 0.0001:
            angle = sign(self.view.yaw) * min(radians(1), abs(self.view.yaw))

            self.view.yaw -= angle
            self.object.applyRotation(Vector((0, 0, -angle)), True)

        self._last_pos = pos
