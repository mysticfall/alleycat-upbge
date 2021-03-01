from abc import ABC
from typing import Generic, TypeVar

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

    def as_game_object(self, obj: Object) -> KX_GameObject:
        # noinspection PyUnresolvedReferences
        return self.object.scene.getGameObjectFromObject(not_empty(obj))


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U
