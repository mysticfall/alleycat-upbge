from typing import Any, Type, TypeVar

from returns.result import Failure, ResultE, Success
from validator_collection import not_empty
# noinspection PyProtectedMember
from validator_collection._decorators import disable_on_env

from alleycat.common import InvalidTypeError

T = TypeVar("T")


@disable_on_env
def of_type(expected: Type[T], obj: Any) -> T:
    if not isinstance(obj, not_empty(expected)):
        raise InvalidTypeError(f"Value {obj} is not of expected type {expected}.")

    return obj


def validate_type(expected: Type[T], obj: Any) -> ResultE[T]:
    try:
        return Success(of_type(expected, obj))
    except InvalidTypeError as e:
        return Failure(e)
