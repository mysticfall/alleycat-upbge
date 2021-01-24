from abc import ABC
from typing import Generic, Iterator, Mapping, TypeVar

from returns.maybe import Maybe, Nothing, Some
from validator_collection import not_empty

T = TypeVar("T")


class Lookup(ABC, Generic[T], Mapping[str, T]):
    def __init__(self, values: Mapping[str, T]) -> None:
        not_empty(values, allow_empty=True)

        self._values = values

        super().__init__()

    def find(self, key: str) -> Maybe[T]:
        return Some(self._values[key]) if key in self._values else Nothing

    def __getitem__(self, key: str) -> T:
        return self._values[key]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __contains__(self, key: object) -> bool:
        return key in self._values
