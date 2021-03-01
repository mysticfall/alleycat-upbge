from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MockVector:
    values: Tuple[float, float]
