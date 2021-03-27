from abc import ABC
from typing import Generic, TypeVar

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID, Object
from rx import Observable
from rx.subject import Subject
from validator_collection import not_empty

from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)


class BaseComponent(Generic[T], LoggingSupport, ReactiveObject, KX_PythonComponent, ABC):
    object: T

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        super().__init__()

        self._updater = Subject()

    @property
    def valid(self) -> bool:
        return True

    @property
    def on_update(self) -> Observable:
        return self._updater

    def update(self) -> None:
        if self.valid:
            self._updater.on_next(None)

    def as_game_object(self, obj: Object) -> KX_GameObject:
        # noinspection PyUnresolvedReferences
        return self.object.scene.getGameObjectFromObject(not_empty(obj))

    def dispose(self) -> None:
        self._updater.on_completed()

        super().dispose()


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
