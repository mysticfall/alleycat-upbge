from collections import OrderedDict

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from dependency_injector.wiring import Provide, inject

from alleycat.game import GameContext
from alleycat.input import InputMap
from alleycat.log import LoggingSupport


class Character(LoggingSupport, ReactiveObject, KX_PythonComponent):
    args = OrderedDict((
        ("name", "Player"),
    ))

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings]) -> None:
        self.name = args["name"]

        self.logger.info("Starting player.")
        self.logger.info("Input map: %s", input_map)

    def update(self) -> None:
        pass
