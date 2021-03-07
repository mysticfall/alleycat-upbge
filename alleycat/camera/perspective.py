from abc import ABC, abstractmethod
from collections import OrderedDict
from itertools import chain
from typing import Final

from bge.types import KX_Camera, KX_GameObject
from bpy.types import Object
from dependency_injector.wiring import Provide, inject

from alleycat.camera import CameraControl
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.control import TurretControl
from alleycat.game import GameContext
from alleycat.input import InputMap


class PerspectiveCamera(TurretControl[KX_Camera], CameraControl, ABC):
    class ArgKeys(ActivatableComponent.ArgKeys):
        PIVOT: Final = "Pivot"
        VIEWPOINT: Final = "Viewpoint"

    args = OrderedDict(chain(TurretControl.args.items(), (
        (ArgKeys.PIVOT, Object),
        (ArgKeys.VIEWPOINT, Object)
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
            self.callbacks.append(lambda: self.process(p, viewpoint.value_or(p)))

        pivot.map(setup).alt(self.logger.warning)

    @abstractmethod
    def process(self, pivot: KX_GameObject, viewpoint: KX_GameObject) -> None:
        pass
