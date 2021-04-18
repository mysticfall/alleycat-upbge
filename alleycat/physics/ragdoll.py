from collections import OrderedDict
from enum import Enum
from functools import reduce
from itertools import chain
from typing import Final, Mapping, Sequence

import rx
from alleycat.reactive import RV, functions as rv
from bge.types import KX_GameObject
from bpy.types import Collection
from dependency_injector.wiring import Provide
from mathutils import Quaternion, Vector
from returns.converters import result_to_maybe
from returns.curry import partial
from returns.functions import identity, tap
from returns.iterables import Fold
from returns.maybe import Maybe
from returns.result import ResultE, Success, safe
from rx import operators as ops
from rx.subject import Subject
from validator_collection import iterable

from alleycat.animation.runtime import Animating, AnimationGraph
from alleycat.common import ArgumentReader
from alleycat.event import EventLoopScheduler
from alleycat.game import BaseComponent, GameContext, require_component
from alleycat.physics import Collider, HitBox


class RagdollState(Enum):
    Idle = 0
    Ragdolling = 1
    Recovering = 2


class Ragdoll(Collider):
    class ArgKeys(BaseComponent.ArgKeys):
        HIT_BOX_COLLECTION: Final = "Hit Box Collection"
        REQUIRED_FORCE: Final = "Required Force"
        INITIAL_DELAY: Final = "Initial Delay"

    args = OrderedDict(chain(BaseComponent.args.items(), (
        (ArgKeys.HIT_BOX_COLLECTION, Collection),
        (ArgKeys.REQUIRED_FORCE, 10.0),
        (ArgKeys.INITIAL_DELAY, 3.0),
    )))

    scheduler: EventLoopScheduler = Provide[GameContext.scheduler]

    # noinspection PyProtectedMember
    ragdoll_state: RV[RagdollState] = rv.from_instance(lambda i: i._on_state_change) \
        .pipe(lambda _: (ops.switch_latest(), ops.start_with(RagdollState.Idle), ops.distinct_until_changed()))

    force: RV[float] = rv.new_view()

    def __init__(self, obj: KX_GameObject) -> None:
        self._on_state_change = Subject()

        super().__init__(obj)

    @property
    def collection(self) -> Collection:
        return self.params["collection"]

    @property
    def head(self) -> Maybe[KX_GameObject]:
        return self.params["head"]

    @property
    def feet(self) -> Sequence[KX_GameObject]:
        return self.params["feet"]

    @property
    def required_force(self) -> float:
        return self.params["required_force"]

    @property
    def initial_delay(self) -> float:
        return self.params["initial_delay"]

    @property
    def hit_boxes(self) -> Sequence[HitBox]:
        return self.params["hit_boxes"]

    @property
    def animation_graph(self) -> AnimationGraph:
        return self.params["animation_graph"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        collection = args \
            .require(Ragdoll.ArgKeys.HIT_BOX_COLLECTION, Collection) \
            .alt(lambda _: ValueError("Missing hit-box collection."))

        hit_boxes = collection \
            .map(lambda c: map(self.as_game_object, c.objects)) \
            .map(lambda children: chain.from_iterable(map(lambda o: o.components, children))) \
            .map(lambda components: tuple(filter(lambda c: isinstance(c, HitBox), components))) \
            .bind(safe(lambda h: iterable(h))) \
            .alt(lambda _: ValueError("Missing origin object for the ragdoll."))

        feet = hit_boxes \
            .map(lambda boxes: filter(lambda b: "foot" in b.object.name.lower(), boxes)) \
            .map(lambda boxes: tuple(map(lambda f: f.object, boxes)))

        head = hit_boxes \
            .map(lambda boxes: filter(lambda b: "head" in b.object.name.lower(), boxes)) \
            .map(lambda boxes: tuple(map(lambda f: f.object, boxes))) \
            .map(safe(lambda boxes: next(iter(boxes)))) \
            .map(result_to_maybe)

        required_force = args \
            .require(Ragdoll.ArgKeys.REQUIRED_FORCE, float) \
            .map(partial(max, 0.0)) \
            .value_or(10.0)

        initial_delay = args \
            .require(Ragdoll.ArgKeys.INITIAL_DELAY, float) \
            .map(partial(max, 0.0)) \
            .value_or(3.0)

        animation_graph = require_component(self.object, Animating).map(lambda a: a.animation_graph)

        result = Fold.collect((
            animation_graph.map(lambda a: ("animation_graph", a)),
            collection.map(lambda c: ("collection", c)),
            hit_boxes.map(lambda h: ("hit_boxes", h)),
            head.map(lambda h: ("head", h)),
            feet.map(lambda f: ("feet", f)),
            Success(("required_force", required_force)),
            Success(("initial_delay", initial_delay)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        velocity = self.on_process.pipe(
            ops.map(lambda _: self.object.worldPosition.copy()),
            ops.timestamp(),
            ops.pairwise(),
            ops.map(lambda v: (v[1].value - v[0].value) / (v[1].timestamp - v[0].timestamp).total_seconds()),
            ops.share())

        acceleration = velocity.pipe(
            ops.timestamp(),
            ops.pairwise(),
            ops.map(lambda v: (v[1].value - v[0].value) / (v[1].timestamp - v[0].timestamp).total_seconds()))

        force = acceleration.pipe(ops.map(lambda a: (self.object.mass * a).length), ops.start_with(0))

        collisions = rx.combine_latest(self.on_collision, force)

        stable = velocity.pipe(
            ops.map(lambda v: v.length_squared <= 0.5),
            ops.distinct_until_changed(),
            ops.debounce(1.0, self.scheduler))

        impacts = rx.timer(self.initial_delay, scheduler=self.scheduler).pipe(
            ops.map(lambda _: collisions),
            ops.switch_latest(),
            ops.filter(lambda v: v[1] > self.required_force * 1000))

        when_ragdoll = impacts.pipe(
            ops.filter(lambda _: self.ragdoll_state != RagdollState.Ragdolling),
            ops.map(lambda _: RagdollState.Ragdolling),
            ops.share())

        when_recovering = when_ragdoll.pipe(
            ops.map(lambda _: stable.pipe(ops.filter(identity), ops.take(1))),
            ops.switch_latest(),
            ops.filter(identity),
            ops.map(lambda _: RagdollState.Recovering),
            ops.share())

        when_idle = when_recovering.pipe(
            ops.map(lambda _: rx.timer(3.0, scheduler=self.scheduler)),
            ops.switch_latest(),
            ops.map(lambda _: RagdollState.Idle),
            ops.share())

        while_ragdoll = when_ragdoll.pipe(
            ops.map(lambda _: self.on_process.pipe(ops.take_until(when_idle))),
            ops.switch_latest(),
            ops.share())

        # noinspection PyTypeChecker
        state = rx.merge(when_ragdoll, when_recovering, when_idle).pipe(
            ops.distinct_until_changed())

        self._on_state_change.on_next(state)

        when_ragdoll.pipe(
            ops.take_until(self.on_dispose)
        ).subscribe(lambda _: self.on_ragdoll(), on_error=self.error_handler)

        while_ragdoll.pipe(
            ops.take_until(self.on_dispose)
        ).subscribe(lambda _: self.while_ragdoll(), on_error=self.error_handler)

        when_recovering.pipe(
            ops.take_until(self.on_dispose)
        ).subscribe(lambda _: self.on_recover(), on_error=self.error_handler)

        when_idle.pipe(
            ops.take_until(self.on_dispose)
        ).subscribe(lambda _: self.on_idle(), on_error=self.error_handler)

    def on_idle(self) -> None:
        self.logger.info("Entering idle state.")

        for box in self.hit_boxes:
            box.deactivate()

        self.animation_graph.active = True

    def on_recover(self) -> None:
        self.logger.info("Starting ragdoll recovery.")

    def on_ragdoll(self) -> None:
        self.logger.info("Start ragdoll state.")

        self.animation_graph.active = False

        for box in self.hit_boxes:
            box.activate()

    def while_ragdoll(self) -> None:
        z = self.object.worldPosition.z

        boxes = self.feet if len(self.feet) > 0 else self.hit_boxes

        # noinspection PyUnresolvedReferences
        origin: Vector = reduce(Vector.__add__, map(lambda b: b.worldPosition, boxes)) / len(boxes)
        origin.z = z

        self.object.worldPosition = origin.copy()

        def apply_rotation(r: Quaternion):
            self.object.worldOrientation = r

        # noinspection PyUnresolvedReferences
        self.head \
            .map(lambda h: h.worldPosition.copy()) \
            .map(tap(lambda h: h.__setattr__("z", z))) \
            .map(lambda h: (origin - h).to_track_quat("-Y", "Z")) \
            .map(apply_rotation)
