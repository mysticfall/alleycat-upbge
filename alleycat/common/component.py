from typing import Generic, TypeVar

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID

from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)


class BaseComponent(Generic[T], LoggingSupport, ReactiveObject, KX_PythonComponent):
    object: T

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        super().__init__()


class IDComponent(Generic[T, U], BaseComponent[T]):
    blenderObject: U
