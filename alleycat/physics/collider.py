from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar

from bge.types import KX_GameObject
from mathutils import Vector
from rx import Observable
from rx.subject import Subject

from alleycat.game import BaseComponent


@dataclass(frozen=True)
class CollisionEvent:
    object: KX_GameObject

    point: Vector

    normal: Vector

    __slots__ = ["object", "point", "normal"]


T = TypeVar("T", bound=KX_GameObject)


class Collider(Generic[T], BaseComponent[T], ABC):

    def __init__(self, obj: T) -> None:
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
