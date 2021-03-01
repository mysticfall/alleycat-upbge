from abc import ABC
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class VectorLike(ABC):
    values: Tuple[float, ...]

    @property
    def x(self) -> float:
        return self.values[0]

    @property
    def y(self) -> float:
        return self.values[1]

    @property
    def z(self) -> float:
        return self.values[2]


@dataclass(frozen=True)
class MockVector(VectorLike):
    pass


@dataclass(frozen=True)
class MockEuler(VectorLike):
    order: str
