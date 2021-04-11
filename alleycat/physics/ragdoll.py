from collections import OrderedDict
from datetime import datetime
from itertools import chain
from typing import Final, Iterable, Mapping

import rx
from alleycat.reactive import RP, RV, functions as rv
from bge.types import KX_GameObject
from bpy.types import Collection
from returns.curry import partial
from returns.iterables import Fold
from returns.result import ResultE, Success
from rx import operators as ops

from alleycat.common import ActivatableComponent, ArgumentReader
from alleycat.physics import Collider, HitBox


class Ragdoll(Collider[KX_GameObject]):
    class ArgKeys(ActivatableComponent.ArgKeys):
        HIT_BOX_COLLECTION: Final = "Hit Box Collection"
        REQUIRED_FORCE: Final = "Required Force"

    args = OrderedDict(chain(ActivatableComponent.args.items(), (
        (ArgKeys.HIT_BOX_COLLECTION, Collection),
        (ArgKeys.REQUIRED_FORCE, 10),
    )))

    _ragdolling: RP[bool] = rv.from_value(False)

    ragdolling: RV[bool] = _ragdolling.as_view()

    force: RV[float] = rv.new_view()

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

    @property
    def collection(self) -> Collection:
        return self.params["collection"]

    @property
    def required_force(self) -> float:
        return self.params["required_force"]

    @property
    def hit_boxes(self) -> Iterable[HitBox]:
        children = map(self.as_game_object, self.collection.objects)
        components = chain.from_iterable(map(lambda o: o.components, children))

        return filter(lambda c: isinstance(c, HitBox), components)

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        collection = args \
            .require(self.ArgKeys.HIT_BOX_COLLECTION, Collection) \
            .alt(lambda _: ValueError("Missing hit-box collection."))

        required_force = args \
            .require(self.ArgKeys.REQUIRED_FORCE, float) \
            .map(partial(max, 0.0)) \
            .value_or(10.0)

        result = Fold.collect((
            collection.map(lambda c: ("collection", c)),
            Success(("required_force", required_force)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))

    def initialize(self) -> None:
        super().initialize()

        velocity = self.on_process.pipe(
            ops.map(lambda _: self.object.worldLinearVelocity.copy()),
            ops.timestamp())

        acceleration = velocity.pipe(
            ops.pairwise(),
            ops.map(lambda v: (v[1].value - v[0].value).length / (v[1].timestamp - v[0].timestamp).total_seconds()))

        self.force = acceleration.pipe(ops.map(lambda a: self.object.mass * a), ops.start_with(0))

        def on_collision():
            if not self._ragdolling:
                self._ragdolling = True
                self._ragdoll_started = datetime.now()

                self.object.suspendPhysics()

                for box in self.hit_boxes:
                    box.activate()

        collisions = rx.combine_latest(self.on_collision, rv.observe(self.force))

        rx.timer(3).pipe(
            ops.map(lambda _: collisions),
            ops.switch_latest(),
            ops.filter(lambda v: v[1] > self.required_force * 1000),
        ).subscribe(lambda _: on_collision(), on_error=self.error_handler)
