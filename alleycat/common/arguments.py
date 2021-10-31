from typing import Type, TypeVar

from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, ResultE, Success
from validator_collection import not_empty

T = TypeVar("T")


class ArgumentReader:

    def __init__(self, args: dict):
        super().__init__()

        self._source = not_empty(args, allow_empty=True)

    @property
    def source(self) -> dict:
        return self._source

    def read(self, key: str, tpe: Type[T]) -> Maybe[T]:
        if not_empty(key) in not_empty(self.source):
            value = self.source[key]

            if isinstance(value, not_empty(tpe)):
                return Some(value)

        return Nothing

    def require(self, key: str, tpe: Type[T]) -> ResultE[T]:
        if not_empty(key) in not_empty(self.source):
            value = self.source[key]

            if not isinstance(value, not_empty(tpe)):
                return Failure(ValueError(f"Component property '{key}' has an invalid value: '{value}'."))

            return Success(value)
        else:
            return Failure(ValueError(f"Missing component property '{key}'."))
