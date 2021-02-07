from collections import OrderedDict

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import NodeTree
from dependency_injector.wiring import Provide, inject

from alleycat.animation.addon import AnimationOutputNode
from alleycat.animation.runtime import RuntimeAnimationContext
from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.input import InputMap
from alleycat.log import LoggingSupport


class AnimationGraph(LoggingSupport, ReactiveObject, KX_PythonComponent):
    args = OrderedDict((
        ("Animation", NodeTree),
    ))

    animation_context: RuntimeAnimationContext

    output: AnimationOutputNode

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings],
            scheduler: EventLoopScheduler = Provide[GameContext.scheduler]) -> None:
        tree: NodeTree = args["Animation"]

        self.animation_context = RuntimeAnimationContext(self.object)

        self.logger.info("Loading animation graph: %s.", tree)

        for node in tree.nodes:
            self.logger.info("Found node: %s.", node)

        try:
            self.output = next(filter(lambda n: isinstance(n, AnimationOutputNode), tree.nodes))
        except StopIteration:
            pass

        self.logger.info("Output node: %s", self.output)

    def update(self) -> None:
        if self.output:
            self.output.advance(self.animation_context)
