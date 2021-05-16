from abc import ABC
from dataclasses import dataclass
from itertools import chain
from typing import Mapping

from bge.types import KX_GameObject
from mathutils import Vector
from returns.iterables import Fold
from returns.result import ResultE, Success
from rx import Observable
from rx.subject import Subject

from alleycat.common import ArgumentReader
from alleycat.game import BaseComponent, require_component


@dataclass(frozen=True)
class CollisionEvent:
    object: KX_GameObject

    point: Vector

    normal: Vector

    __slots__ = ["object", "point", "normal"]


class Collider(BaseComponent[KX_GameObject]):

    def __init__(self, obj: KX_GameObject) -> None:
        super().__init__(obj)

        self._on_collision = Subject()

    def initialize(self) -> None:
        super().initialize()

        def callback(obj: KX_GameObject, point: Vector, normal: Vector):
            evt = CollisionEvent(obj, point, normal)

            self.logger.debug("Collision detected: %s.", evt)

            if self.active:
                self._on_collision.on_next(CollisionEvent(obj, point, normal))

        self.object.collisionCallbacks.append(callback)

    @property
    def on_collision(self) -> Observable:
        return self._on_collision

    def dispose(self) -> None:
        self._on_collision.dispose()

        super().dispose()


class Physical(BaseComponent[KX_GameObject], ABC):

    @property
    def collider(self) -> Collider:
        return self.params["collider"]

    def init_params(self, args: ArgumentReader) -> ResultE[Mapping]:
        result = Fold.collect((
            require_component(self.object, Collider).map(lambda c: ("collider", c)),
        ), Success(())).map(chain).map(dict)

        inherited = super().init_params(args)

        return result.bind(lambda a: inherited.map(lambda b: a | b))
