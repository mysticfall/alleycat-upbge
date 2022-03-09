from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar

TSource = TypeVar("TSource", covariant=True)


@dataclass(frozen=True)
class Event(Generic[TSource], ABC):
    source: TSource

    def __post_init__(self) -> None:
        if self.source is None:
            raise ValueError("Argument 'source' is missing.")
