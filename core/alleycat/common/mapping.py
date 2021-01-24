from typing import Any, Mapping, Type, TypeVar

from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success
from validator_collection import not_empty

T = TypeVar("T")


class MapReader:

    def __init__(self, args: Mapping[str, Any]):
        super().__init__()

        if args is None:
            raise ValueError("Argument 'args' is missing.")

        self._source = args

    @property
    def source(self) -> Mapping[str, Any]:
        return self._source

    def read(self, key: str, tpe: Type[T]) -> Maybe[T]:
        if not_empty(key) in self.source:
            value = self.source[key]

            if isinstance(value, not_empty(tpe)):
                return Some(value)

        return Nothing

    def require(self, key: str, tpe: Type[T]) -> ResultE[T]:
        if not_empty(key) in self.source:
            value = self.source[key]

            if value is not None:
                if not isinstance(value, not_empty(tpe)):
                    return Failure(ValueError(f"Argument '{key}' has an invalid value: '{value}'."))

                return Success(value)

        return Failure(ValueError(f"Missing required argument '{key}'."))
