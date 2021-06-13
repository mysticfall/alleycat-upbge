from abc import ABC
from collections import OrderedDict
from itertools import chain
from typing import Final, Mapping

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject
from dependency_injector.wiring import inject
from mathutils import Matrix, Vector
from returns.iterables import Fold
from returns.maybe import Maybe
from returns.result import ResultE, Success, safe
from rx import operators as ops

from alleycat.animation import AnimationResult
from alleycat.animation.addon import MixAnimationNode
from alleycat.animation.runtime import Animating, AnimationGraph
from alleycat.common import ArgumentReader
from alleycat.game import BaseComponent, require_component


class Locomotion(BaseComponent[KX_GameObject], ABC):
    movement: RP[Vector] = rv.from_value(Vector((0, 0, 0)))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)


class Mobile(BaseComponent[KX_GameObject], ABC):

    @property
    def locomotion(self) -> Locomotion:
        return self.params["locomotion"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        result = Fold.collect((
            require_component(self.object, Locomotion).map(lambda v: ("locomotion", v)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))


class RootMotionLocomotion(Locomotion):
    class ArgKeys(BaseComponent.ArgKeys):
        MIXER: Final = "Mixer Node"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.MIXER, "Mix"),
    )))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @property
    def animation_graph(self) -> AnimationGraph:
        return self.params["animation_graph"]

    @property
    def root_bone_mat(self) -> Maybe[Matrix]:
        return self.params["root_bone_mat"]

    @property
    def mixer(self) -> MixAnimationNode:
        return self.params["mixer"]

    @inject
    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        animation_graph = require_component(self.object, Animating) \
            .map(lambda a: a.animation_graph)

        root_bone_mat = animation_graph \
            .map(lambda a: a.root_channel.map(lambda c: c.bone.bone_mat))

        mixer_key = args.read(RootMotionLocomotion.ArgKeys.MIXER, str).value_or("Mix")

        @safe
        def find_mixer(graph: AnimationGraph) -> ResultE[MixAnimationNode]:
            # noinspection PyTypeChecker
            return graph.tree.nodes[mixer_key]

        mixer = animation_graph \
            .bind(find_mixer) \
            .alt(lambda _: ValueError(f"Failed to find a mixer node: '{mixer_key}'."))

        result = Fold.collect((
            animation_graph.map(lambda a: ("animation_graph", a)),
            root_bone_mat.map(lambda b: ("root_bone_mat", b)),
            mixer.map(lambda m: ("mixer", m)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        def process_result(result: AnimationResult) -> None:
            mat = self.root_bone_mat.or_else_call(lambda: Matrix.Identity(3)).inverted()

            # noinspection PyUnresolvedReferences
            self.object.applyMovement(result.offset @ mat, True)

        self.animation_graph.on_advance \
            .pipe(ops.take_until(self.on_dispose)) \
            .subscribe(process_result, on_error=self.error_handler)

    def process(self) -> None:
        super().process()

        # noinspection PyUnresolvedReferences
        self.mixer.inputs["Mix"].default_value = self.movement.y
