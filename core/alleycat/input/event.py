from abc import ABC
from typing import Generic, TypeVar

from alleycat.event import Event

TSource = TypeVar("TSource")


class InputEvent(Generic[TSource], Event[TSource], ABC):
    pass
