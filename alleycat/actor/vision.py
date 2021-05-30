import random
from abc import ABC
from collections import OrderedDict
from datetime import datetime, timedelta
from itertools import chain
from typing import Final, Mapping, Optional

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject
from mathutils import Vector
from returns.curry import partial
from returns.iterables import Fold
from returns.result import ResultE, Success, safe

from alleycat.animation.addon import PlayActionNode
from alleycat.animation.runtime import Animating, AnimationGraph
from alleycat.common import ArgumentReader
from alleycat.event import EventLoopScheduler
from alleycat.game import BaseComponent, require_component


class Vision(BaseComponent[KX_GameObject], ABC):
    looking_at: RP[Vector] = rv.from_value(Vector((0, -1, 0)))

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)


class Sighted(BaseComponent[KX_GameObject], ABC):

    @property
    def vision(self) -> Vision:
        return self.params["vision"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        result = Fold.collect((
            require_component(self.object, Vision).map(lambda v: ("vision", v)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))


class Eyes(Vision):
    class ArgKeys(BaseComponent.ArgKeys):
        BLINKS_PER_MINUTE: Final = "Blinks Per Minute"
        BLINK_INTERVAL_VARIANCE: Final = "Blink Interval Variance"
        BLINK_ACTION_NODE: Final = "Blink Action Node"

    args = OrderedDict(chain(Vision.args.items(), (
        (ArgKeys.BLINKS_PER_MINUTE, 13.5),
        (ArgKeys.BLINK_INTERVAL_VARIANCE, 0.1),
        (ArgKeys.BLINK_ACTION_NODE, "Eye Blink")
    )))

    _blink_at: Optional[datetime] = None

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self.animation_graph.scheduler

    @property
    def animation_graph(self) -> AnimationGraph:
        return self.params["animation_graph"]

    @property
    def action_node(self) -> PlayActionNode:
        return self.params["action_node"]

    @property
    def blinks_per_minute(self) -> float:
        return self.params["blinks_per_minute"]

    @property
    def blink_interval_variance(self) -> float:
        return self.params["blink_interval_variance"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        animation_graph = require_component(self.object, Animating) \
            .map(lambda a: a.animation_graph)

        node_key = args.read(Eyes.ArgKeys.BLINK_ACTION_NODE, str).value_or("Eye Blink")

        blinks_per_minute = args \
            .read(Eyes.ArgKeys.BLINKS_PER_MINUTE, float) \
            .map(partial(max, 0.0)) \
            .value_or(13.5)

        blink_interval_variance = args \
            .read(Eyes.ArgKeys.BLINK_INTERVAL_VARIANCE, float) \
            .map(partial(max, 0.0)) \
            .map(partial(min, 1.0)) \
            .value_or(0.1)

        @safe
        def find_node(graph: AnimationGraph) -> ResultE[PlayActionNode]:
            # noinspection PyTypeChecker
            return graph.tree.nodes[node_key]

        action_node = animation_graph \
            .bind(find_node) \
            .alt(lambda _: ValueError(f"Failed to find the action node: '{node_key}'."))

        result = Fold.collect((
            animation_graph.map(lambda a: ("animation_graph", a)),
            action_node.map(lambda a: ("action_node", a)),
            Success(("blinks_per_minute", blinks_per_minute)),
            Success(("blink_interval_variance", blink_interval_variance))
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def process(self) -> None:
        super().process()

        if self.blinks_per_minute == 0:
            return

        now = self.scheduler.now

        if not self._blink_at:
            blink_in_seconds = 60.0 / self.blinks_per_minute
            blink_in_seconds *= 1 + self.blink_interval_variance * (random.random() - 0.5)

            self._blink_at = now + timedelta(0, blink_in_seconds)
        elif now > self._blink_at:
            self.action_node.active = True
            self._blink_at = None
