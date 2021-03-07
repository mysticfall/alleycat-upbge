from collections import OrderedDict
from itertools import chain
from typing import Final

from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from dependency_injector.wiring import Provide, inject
from returns.curry import partial

from alleycat.camera import CameraControl
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.control import TurretControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class FirstPersonCamera(TurretControl[KX_Camera], CameraControl):
    class ArgKeys(ActivatableComponent.ArgKeys):
        PIVOT: Final = "Pivot"

    args = OrderedDict(chain(TurretControl.args.items(), (
        (ArgKeys.PIVOT, Object),
    )))

    def __init__(self, obj: KX_Camera) -> None:
        super().__init__(obj=obj)

    # noinspection PyUnusedLocal
    @inject
    def start(self, args: dict, input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        super().start(args)

        props = ArgumentReader(args)

        pivot = props.require(self.ArgKeys.PIVOT, Object).map(self.as_game_object)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.PIVOT, pivot)

        def setup(p: KX_GameObject):
            self.callbacks.append(partial(self.process, p))

        pivot.map(setup).alt(self.logger.warning)

    def process(self, pivot: KX_GameObject) -> None:
        assert pivot

        mat = self.rotation.to_matrix()

        # noinspection PyUnresolvedReferences
        orientation = pivot.worldOrientation @ mat @ self.base_rotation

        self.object.worldOrientation = orientation
        self.object.worldPosition = pivot.worldPosition
