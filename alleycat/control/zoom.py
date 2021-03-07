from abc import ABC
from typing import Generic, TypeVar

from alleycat.reactive import RP, functions as rv
from bge.types import KX_GameObject

from alleycat.common import ActivatableComponent

T = TypeVar("T", bound=KX_GameObject)


class ZoomControl(Generic[T], ActivatableComponent[T], ABC):

    distance: RP[float] = rv.from_value(1.0).map(lambda _, v: max(v, 0.0))

    def __init__(self, obj: T) -> None:
        super().__init__(obj)
