from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from alleycat.reactive import functions as rv
from bge.types import KX_GameObject
from bpy.types import NodeTree, Object
from dependency_injector.wiring import Provide, inject
from mathutils import Vector
from returns.iterables import Fold
from returns.maybe import Maybe
from returns.result import ResultE, Success, safe
from rx import operators as ops

from alleycat.animation import AnimationResult, Animator
from alleycat.animation.addon import AnimationNodeTree, MixAnimationNode
from alleycat.animation.runtime import GameObjectAnimator
from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.input import Axis2DBinding, InputMap


class AnimationGraph(ActivatableComponent[KX_GameObject]):
    class ArgKeys(ActivatableComponent.ArgKeys):
        ANIMATION: Final = "Animation"
        RM_TARGET: Final = "Root Motion Target"

    args = OrderedDict((
        (ArgKeys.ANIMATION, NodeTree),
        (ArgKeys.RM_TARGET, Object)
    ))

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

    @property
    def animator(self) -> Animator:
        return self.params["animator"]

    @property
    def tree(self) -> AnimationNodeTree:
        return self.params["tree"]

    @property
    def mixer(self) -> MixAnimationNode:
        return self.params["mixer"]

    @property
    def move_input(self) -> Axis2DBinding:
        return self.params["move_input"]

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self.params["scheduler"]

    @inject
    def init_params(
            self,
            args: ArgumentReader,
            input_map: InputMap = Provide[GameContext.input.mappings],
            scheduler: EventLoopScheduler = Provide[GameContext.scheduler]) -> ResultE[Mapping]:
        @safe
        def find_mixer(t: AnimationNodeTree) -> MixAnimationNode:
            return t.nodes.get("Mix")

        @safe
        def find_input() -> Axis2DBinding:
            return input_map["view"]["move"]

        tree = args.require(self.ArgKeys.ANIMATION, NodeTree)
        mixer = tree.bind(find_mixer).alt(lambda _: ValueError("Failed to find a mixer node."))
        move_input = find_input().alt(lambda _: ValueError("Failed to find an input."))

        result = Fold.collect((
            tree.map(lambda t: ("tree", t)),
            mixer.map(lambda m: ("mixer", m)),
            move_input.map(lambda i: ("move_input", i)),
            Success(("scheduler", scheduler)),
            Success(("animator", GameObjectAnimator(self.object)))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        self.logger.info("Loading animation graph: %s.", self.tree)

        self.tree.start()

        for node in self.tree.nodes:
            self.logger.info("Found node: %s.", node)

        def move(value: Vector):
            self.mixer.inputs["Mix"].default_value = value.y

        rv \
            .observe(self.move_input.value) \
            .pipe(ops.filter(lambda _: self.active), ops.take_until(self.on_dispose)) \
            .subscribe(move, on_error=self.error_handler)

        def advance(delta: float) -> Maybe[AnimationResult]:
            self.animator.time_delta = delta

            return self.tree.advance(self.animator)

        def process_result(result: AnimationResult) -> None:
            # noinspection PyUnresolvedReferences
            rm = result.offset
            rm.z = 0

            self.object.applyMovement(rm, True)

        deltas = self.scheduler.on_process.pipe(
            ops.pairwise(),
            ops.map(lambda t: (t[1] - t[0]).total_seconds()),
            ops.filter(lambda _: self.active))

        deltas.subscribe(lambda d: advance(d).map(process_result).value_or(None), on_error=self.error_handler)

        super().initialize()
