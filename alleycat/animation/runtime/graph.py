from abc import ABC
from collections import OrderedDict
from datetime import datetime
from functools import cached_property
from itertools import chain
from typing import Final, Mapping

from bge.types import BL_ArmatureChannel, BL_ArmatureObject, KX_GameObject
from bpy.types import NodeTree, Object
from dependency_injector.wiring import Provide
from returns.iterables import Fold
from returns.maybe import Maybe, Nothing, Some
from returns.result import ResultE, Success
from rx import Observable
from rx.subject import Subject

from alleycat.animation import Animator
from alleycat.animation.addon import AnimationNodeTree
from alleycat.animation.runtime import GameObjectAnimator
from alleycat.common import ArgumentReader
from alleycat.event import EventLoopScheduler
from alleycat.game import BaseComponent, GameContext, require_component
from alleycat.input import InputMap


class AnimationGraph(BaseComponent[BL_ArmatureObject]):
    class ArgKeys(BaseComponent.ArgKeys):
        ANIMATION_TREE: Final = "Animation Tree"
        RIG: Final = "Rig"
        ROOT_BONE: Final = "Root Bone"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.ANIMATION_TREE, NodeTree),
        (ArgKeys.RIG, Object),
        (ArgKeys.ROOT_BONE, ""),
    )))

    input_map: InputMap = Provide[GameContext.input.mappings]

    scheduler: EventLoopScheduler = Provide[GameContext.scheduler]

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

        self._on_advance = Subject()
        self._last_timestamp: Maybe[datetime] = Nothing

    @property
    def rig(self) -> BL_ArmatureObject:
        return self.params["rig"]

    @cached_property
    def animator(self) -> Animator:
        root_bone = self.params["root_bone"].value_or(None)

        return GameObjectAnimator(self.rig, root_bone=root_bone)

    @cached_property
    def root_channel(self) -> Maybe[BL_ArmatureChannel]:
        return self.params["root_bone"] \
            .map(lambda b: self.rig.channels[b]) \
            .bind(Maybe.from_optional)

    @property
    def tree(self) -> AnimationNodeTree:
        return self.params["tree"]

    @property
    def on_advance(self) -> Observable:
        return self._on_advance

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        tree = args.require(AnimationGraph.ArgKeys.ANIMATION_TREE, NodeTree)
        root_bone = args.read(AnimationGraph.ArgKeys.ROOT_BONE, str) \
            .map(str.strip) \
            .bind(lambda s: Some(s) if len(s) > 0 else Nothing)

        rig = require_type(
            args.read(AnimationGraph.ArgKeys.RIG, Object).map(as_game_object).value_or(self.object),
            BL_ArmatureObject)

        result = Fold.collect((
            rig.map(lambda r: ("rig", r)),
            tree.map(lambda t: ("tree", t)),
            Success(("root_bone", root_bone)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        self.tree.start()

        for node in self.tree.nodes:
            self.logger.debug("Found node: %s.", node)

        super().initialize()

    def process(self) -> None:
        timestamp = self.scheduler.now
        last_timestamp = self._last_timestamp.value_or(timestamp)

        self._last_timestamp = Some(timestamp)

        delta = (timestamp - last_timestamp).total_seconds()

        if delta > 0:
            self.animator.time_delta = delta

            result = self.tree.advance(self.animator)

            self._on_advance.on_next(result)

    def dispose(self) -> None:
        self._on_advance.dispose()
        super().dispose()


class Animating(BaseComponent[KX_GameObject], ABC):

    @property
    def animator(self) -> Animator:
        return self.animation_graph.animator

    @property
    def animation_graph(self) -> AnimationGraph:
        return self.params["animation_graph"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        animation_graph = self.require_component(AnimationGraph)

        result = Fold.collect((
            animation_graph.map(lambda a: ("animation_graph", a)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
