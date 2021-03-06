from collections import OrderedDict
from itertools import chain
from typing import Final

from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from mathutils.geometry import distance_point_to_plane
from returns.curry import curry, partial

from alleycat.camera import CameraControl
from alleycat.common import ArgumentReader
from alleycat.control import TurretControl, ZoomControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class ThirdPersonCamera(TurretControl[KX_Camera], ZoomControl[KX_Camera], CameraControl):
    class ArgKeys(TurretControl.ArgKeys, ZoomControl.ArgKeys):
        PIVOT: Final = "Pivot"
        VIEWPOINT: Final = "Viewpoint"

    args = OrderedDict(chain(TurretControl.args.items(), ZoomControl.args.items(), (
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

        pivot = props.require(self.ArgKeys.PIVOT, Object).map(self.as_game_object)
        viewpoint = props.read(self.ArgKeys.VIEWPOINT, Object).map(self.as_game_object)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.PIVOT, pivot)
        self.logger.debug("args['%s'] = %s", self.ArgKeys.VIEWPOINT, viewpoint)

        def setup(p: KX_GameObject):
            self.callbacks.append(partial(self.process, p, viewpoint.value_or(p)))  # type:ignore

        pivot.map(setup).alt(self.logger.warning)

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
