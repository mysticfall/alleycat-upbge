from collections import OrderedDict
from math import radians

import bge
from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent, KX_Scene
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from numpy import sign

from alleycat.camera import CameraManager
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
        manager: KX_GameObject = scene.getGameObjectFromObject(args["camera"])

        for comp in manager.components:
            if isinstance(comp, CameraManager):
                self.manager = comp
                break

        self._last_pos = self.object.worldPosition.copy()

        self.logger.info("Input map: %s", input_map)
        self.logger.info("Camera Manager: %s", manager)

    def update(self) -> None:
        pos = self.object.worldPosition.copy()

        if not self.manager.valid:
            return

        view = self.manager.active_camera

        if not view:
            return

        if (pos - self._last_pos).length_squared > 0.0001:
            angle = sign(view.yaw) * min(radians(5), abs(view.yaw))

            view.yaw -= angle
            self.object.parent.applyRotation(Vector((0, 0, -angle)), True)

        self._last_pos = pos
