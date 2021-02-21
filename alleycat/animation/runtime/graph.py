from collections import OrderedDict
from typing import Optional

from alleycat.reactive import ReactiveObject, functions as rv
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import NodeTree
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from rx import operators as ops
from validator_collection import not_empty

from alleycat.animation.addon import AnimationNodeTree, MixAnimationNode
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

    tree: AnimationNodeTree

    timestamp: Optional[float]

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings],
            scheduler: EventLoopScheduler = Provide[GameContext.scheduler]) -> None:
        self.tree = not_empty(args["Animation"])

        self.animation_context = RuntimeAnimationContext(self.object)

        self.logger.info("Loading animation graph: %s.", self.tree)

        self.tree.start(self.animation_context)

        for node in self.tree.nodes:
            self.logger.info("Found node: %s.", node)

        mixer: MixAnimationNode = self.tree.nodes.get("Mix")

        self.logger.info("Mixer node: %s", mixer)

        def move(value: Vector):
            mixer.inputs["Mix"].default_value = value.y

        move_input = input_map["view"]["move"]

        rv.observe(move_input.value).subscribe(move, on_error=self.error_handler)

        self.last_rm_loc = Vector((0, 0, 0))

        def process(delta: float):
            self.animation_context.time_delta = delta
            offset = self.tree.advance(self.animation_context)

            rm = self.last_rm_loc - offset
            rm.z = 0

            self.last_rm_loc = offset

            if 0 < rm.length_squared < 0.001:
                self.object.applyMovement(rm, True)

        deltas = scheduler.on_process.pipe(
            ops.pairwise(),
            ops.map(lambda t: (t[1] - t[0]).total_seconds()))

        deltas.subscribe(process, on_error=self.error_handler)

    def update(self) -> None:
        pass
