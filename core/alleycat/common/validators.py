from typing import Any, Type, TypeVar

from returns.maybe import Maybe, Nothing
from returns.result import Failure, Result, ResultE
from validator_collection import not_empty
# noinspection PyProtectedMember
from validator_collection._decorators import disable_on_env

from alleycat.common import InvalidTypeError

T = TypeVar("T")


def create_error(obj: Any, expected: type) -> InvalidTypeError:
    return InvalidTypeError(
        f"Value {obj} is not of expected type '{expected.__name__}' (actual: '{type(obj).__name__}').")


@disable_on_env
def of_type(obj: Any, expected: Type[T]) -> T:
    if not isinstance(obj, not_empty(expected)):
        raise create_error(obj, expected)

    return obj


def maybe_type(obj: Any, expected: Type[T]) -> Maybe[T]:
    return Maybe.from_value(obj) if isinstance(obj, not_empty(expected)) else Nothing


def require_type(obj: Any, expected: Type[T]) -> ResultE[T]:
    if not isinstance(obj, not_empty(expected)):
        return Failure(create_error(obj, expected))

    return Result.from_value(obj)
