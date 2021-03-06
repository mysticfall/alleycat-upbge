from collections import OrderedDict
from itertools import chain
from typing import Final

from alleycat.reactive import RP, functions as rv
from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane
from returns.curry import curry, partial
from rx import Observable
from rx import operators as ops

from alleycat.camera import CameraControl
from alleycat.common import ArgumentReader
from alleycat.control import TurretControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class ThirdPersonCamera(TurretControl[KX_Camera], CameraControl):
    class ArgKeys(TurretControl.ArgKeys):
        ZOOM_INPUT: Final = "Zoom Input"
        ZOOM_SENSITIVITY: Final = "Zoom Sensitivity"
        PIVOT: Final = "Pivot"
        VIEWPOINT: Final = "Viewpoint"

    args = OrderedDict(chain(TurretControl.args.items(), (
        (ArgKeys.ZOOM_INPUT, "view/zoom"),
        (ArgKeys.ZOOM_SENSITIVITY, 1.0),
        (ArgKeys.PIVOT, Object),
        (ArgKeys.VIEWPOINT, Object),
    )))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj=obj)

    # noinspection PyUnusedLocal
    @inject
    def start(self, args: dict, input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        super().start(args)

        props = ArgumentReader(args)

        # noinspection PyTypeChecker,PyShadowingBuiltins
        input = props.require(self.ArgKeys.ZOOM_INPUT, str) \
            .map(lambda s: s.split("/")) \
            .bind(input_map.observe)

        pivot = props.require(self.ArgKeys.PIVOT, Object).map(self.as_game_object)
        sensitivity = props.read(self.ArgKeys.ZOOM_SENSITIVITY, float).value_or(1.0)
        viewpoint = props.read(self.ArgKeys.VIEWPOINT, Object).map(self.as_game_object)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.ZOOM_INPUT, input)
        self.logger.debug("args['%s'] = %s", self.ArgKeys.PIVOT, pivot)
        self.logger.debug("args['%s'] = %s", self.ArgKeys.ZOOM_SENSITIVITY, sensitivity)
        self.logger.debug("args['%s'] = %s", self.ArgKeys.VIEWPOINT, viewpoint)

        def zoom(value: float):
            self.distance = max(self.distance - value * 0.1 * sensitivity, 0)

        def setup(i: Observable, p: KX_GameObject):
            self.callbacks.append(partial(self.process, p, viewpoint.value_or(p)))  # type:ignore

            i.pipe(ops.take_until(self.on_dispose)).subscribe(zoom, on_error=self.error_handler)

        init = input.bind(lambda i: pivot.map(lambda p: setup(i, p)))

        init.alt(self.logger.warning)

    @curry
    def process(self, pivot: KX_GameObject, viewpoint: KX_GameObject) -> None:
        assert pivot
        assert viewpoint

        # noinspection PyUnresolvedReferences
        up_axis = pivot.worldOrientation @ Vector((0, 0, 1))

        height = distance_point_to_plane(viewpoint.worldPosition, pivot.worldPosition, up_axis)

        mat = self.rotation.to_matrix()

        # noinspection PyUnresolvedReferences
        orientation = pivot.worldOrientation @ mat @ self.base_rotation

        # noinspection PyUnresolvedReferences
        offset = pivot.worldOrientation @ mat @ Vector((0, -1, 0)) * self.distance

        self.object.worldOrientation = orientation

        # noinspection PyUnresolvedReferences
        self.object.worldPosition = pivot.worldPosition - offset + up_axis * height * 0.8
