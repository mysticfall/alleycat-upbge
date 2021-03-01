from abc import ABC
from typing import Generic, Type, TypeVar

from alleycat.reactive import ReactiveObject
from bge.types import KX_GameObject, KX_PythonComponent
from bpy.types import ID
from returns.curry import curry
from returns.result import Failure, ResultE, Success
from validator_collection import not_empty

from alleycat.log import LoggingSupport

T = TypeVar("T", bound=KX_GameObject)
U = TypeVar("U", bound=ID)
V = TypeVar("V")


class BaseComponent(Generic[T], LoggingSupport, ReactiveObject, KX_PythonComponent, ABC):
    object: T

    # noinspection PyUnusedLocal
    def __init__(self, obj: T):
        super().__init__()

    @staticmethod
    @curry
    def read_arg(args: dict, key: str, tpe: Type[V]) -> ResultE[V]:
        if not_empty(key) in not_empty(args):
            value = args[key]

            if not isinstance(value, not_empty(tpe)):
                return Failure(ValueError(f"Component property '{key}' has an invalid value: '{value}'."))

            return Success(value)
        else:
            return Failure(ValueError(f"Missing component property '{key}'."))


class IDComponent(Generic[T, U], BaseComponent[T], ABC):
    blenderObject: U
