from collections import OrderedDict
from typing import Optional

from alleycat.reactive import functions as rv
from bge.types import KX_GameObject
from bpy.types import NodeTree
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from returns.maybe import Maybe
from rx import operators as ops
from validator_collection import not_empty

from alleycat.animation import AnimationResult
from alleycat.animation.addon import AnimationNodeTree, MixAnimationNode
from alleycat.animation.runtime import GameObjectAnimator
from alleycat.common import ActivatableComponent
from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.input import InputMap


class AnimationGraph(ActivatableComponent[KX_GameObject]):
    args = OrderedDict((
        ("Animation", NodeTree),
    ))

    animator: GameObjectAnimator

    tree: AnimationNodeTree

    timestamp: Optional[float]

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

    @inject
    def start(
            self,
            args: dict,
            input_map: InputMap = Provide[GameContext.input.mappings],
            scheduler: EventLoopScheduler = Provide[GameContext.scheduler]) -> None:
        self.tree = not_empty(args["Animation"])

        self.animator = GameObjectAnimator(self.object)

        self.logger.info("Loading animation graph: %s.", self.tree)

        self.tree.start()

        for node in self.tree.nodes:
            self.logger.info("Found node: %s.", node)

        mixer: MixAnimationNode = self.tree.nodes.get("Mix")

        self.logger.info("Mixer node: %s", mixer)

        def move(value: Vector):
            mixer.inputs["Mix"].default_value = value.y

        move_input = input_map["view"]["move"]

        rv \
            .observe(move_input.value) \
            .pipe(ops.filter(lambda _: self.active)) \
            .subscribe(move, on_error=self.error_handler)

        def advance(delta: float) -> Maybe[AnimationResult]:
            self.animator.time_delta = delta

            return self.tree.advance(self.animator)

        def process_result(result: AnimationResult) -> None:
            # noinspection PyUnresolvedReferences
            rm = result.offset
            rm.z = 0

            self.object.parent.applyMovement(rm, True)

        deltas = scheduler.on_process.pipe(
            ops.pairwise(),
            ops.map(lambda t: (t[1] - t[0]).total_seconds()),
            ops.filter(lambda _: self.active))

        deltas.subscribe(lambda d: advance(d).map(process_result).value_or(None), on_error=self.error_handler)

    def update(self) -> None:
        pass
