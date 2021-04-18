from abc import ABC
from collections import OrderedDict
from datetime import datetime
from functools import cached_property
from itertools import chain
from typing import Final, Mapping

from bge.types import KX_GameObject
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


class AnimationGraph(BaseComponent[KX_GameObject]):
    class ArgKeys(BaseComponent.ArgKeys):
        ANIMATION_TREE: Final = "Animation Tree"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.ANIMATION_TREE, NodeTree),
    )))

    input_map: InputMap = Provide[GameContext.input.mappings]

    scheduler: EventLoopScheduler = Provide[GameContext.scheduler]

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__(obj)

        self._on_advance = Subject()
        self._last_timestamp: Maybe[datetime] = Nothing

    @cached_property
    def animator(self) -> Animator:
        return GameObjectAnimator(self.object)

    @property
    def tree(self) -> AnimationNodeTree:
        return self.params["tree"]

    @property
    def on_advance(self) -> Observable:
        return self._on_advance

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        tree = args.require(AnimationGraph.ArgKeys.ANIMATION_TREE, NodeTree)

        result = Fold.collect((
            tree.map(lambda t: ("tree", t)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        self.tree.start()

        for node in self.tree.nodes:
            self.logger.debug("Found node: %s.", node)

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
    class ArgKeys(BaseComponent.ArgKeys):
        ANIMATION_TARGET: Final = "Animation Target"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.ANIMATION_TARGET, Object),
    )))

    @property
    def animator(self) -> Animator:
        return self.animation_graph.animator

    @property
    def animation_graph(self) -> AnimationGraph:
        return self.params["animation_graph"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        # noinspection PyTypeChecker
        animation_graph = args \
            .require(self.ArgKeys.ANIMATION_TARGET, Object) \
            .map(self.as_game_object) \
            .bind(lambda o: require_component(o, AnimationGraph))

        result = Fold.collect((
            animation_graph.map(lambda a: ("animation_graph", a)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
