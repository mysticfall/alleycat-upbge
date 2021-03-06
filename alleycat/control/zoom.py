from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Generic, TypeVar

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject
from dependency_injector.wiring import Provide, inject
from rx import Observable, operators as ops

from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.game import GameContext
from alleycat.input import InputMap

T = TypeVar("T", bound=KX_GameObject)


class ZoomControl(Generic[T], ActivatableComponent[T], ABC):
    class ArgKeys(ActivatableComponent.ArgKeys):
        ZOOM_INPUT: Final = "Zoom Input"
        ZOOM_SENSITIVITY: Final = "Zoom Sensitivity"

    args = OrderedDict(chain(ActivatableComponent.args.items(), (
        (ArgKeys.ZOOM_INPUT, "view/zoom"),
        (ArgKeys.ZOOM_SENSITIVITY, 1.0),
    )))

    distance: RP[float] = rv.from_value(1.0).map(lambda _, v: max(v, 0.0))

    def __init__(self, obj: T) -> None:
        super().__init__(obj)

    @inject
    def start(self, args: dict, input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        super().start(args)

        props = ArgumentReader(args)

        input_key = props.require(self.ArgKeys.ZOOM_INPUT, str)

        # noinspection PyTypeChecker
        input_events = input_key.map(lambda s: s.split("/")).bind(input_map.observe)

        sensitivity = props.read(self.ArgKeys.ZOOM_SENSITIVITY, float).value_or(1.0)

        self.logger.debug("args['%s'] = %s", self.ArgKeys.ZOOM_INPUT, input_key)
        self.logger.debug("args['%s'] = %s", self.ArgKeys.ZOOM_SENSITIVITY, sensitivity)

        def zoom(value: float):
            self.distance = max(self.distance - value * 0.1 * sensitivity, 0)

        def setup(o: Observable):
            o.pipe(ops.take_until(self.on_dispose)).subscribe(zoom, on_error=self.error_handler)

        input_events.map(setup).alt(self.logger.warning)
