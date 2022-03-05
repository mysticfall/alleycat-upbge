from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Tuple


@dataclass(frozen=True)
class Point2D(Iterable):
    x: float

    y: float

    __slots__ = ("x", "y")

    @property
    def tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    @staticmethod
    def from_tuple(value: Tuple[float, float]) -> Point2D:
        if value is None:
            raise ValueError("Argument 'value' is required.")

        return Point2D(value[0], value[1])

    def copy(self, x: Optional[float] = None, y: Optional[float] = None) -> Point2D:
        return Point2D(x if x is not None else self.x, y if y is not None else self.y)

    def __add__(self, other: Point2D) -> Point2D:
        if other is None:
            raise ValueError("Cannot perform the operation on None.")

        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point2D) -> Point2D:
        if other is None:
            raise ValueError("Cannot perform the operation on None.")

        return self + (-other)

    def __mul__(self, number: float) -> Point2D:
        return Point2D(self.x * number, self.y * number)

    def __truediv__(self, number: float) -> Point2D:
        return Point2D(self.x / number, self.y / number)

    def __neg__(self) -> Point2D:
        return Point2D(-self.x, -self.y)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
