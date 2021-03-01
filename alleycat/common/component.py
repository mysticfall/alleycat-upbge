from abc import ABC
from typing import Callable, Generic, List, TypeVar

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID, Object
from validator_collection import not_empty

from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)


class BaseComponent(Generic[T], LoggingSupport, ReactiveObject, KX_PythonComponent, ABC):
    object: T

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        super().__init__()

        self._callbacks: List[Callable[[], None]] = []

    @property
    def valid(self) -> bool:
        return True

    @property
    def callbacks(self) -> List[Callable[[], None]]:
        return self._callbacks

    def update(self) -> None:
        if self.valid:
            for callback in self.callbacks:
                callback()

    def as_game_object(self, obj: Object) -> KX_GameObject:
        # noinspection PyUnresolvedReferences
        return self.object.scene.getGameObjectFromObject(not_empty(obj))

    def dispose(self) -> None:
        self.callbacks.clear()

        super().dispose()


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U
