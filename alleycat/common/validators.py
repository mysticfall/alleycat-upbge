from typing import Any, Type, TypeVar

from validator_collection import not_empty
# noinspection PyProtectedMember
from validator_collection._decorators import disable_on_env

from alleycat.common import InvalidTypeError

T = TypeVar("T")


@disable_on_env
def of_type(obj: Any, expected: Type[T]) -> T:
    if not isinstance(obj, not_empty(expected)):
        raise InvalidTypeError(f"Value {obj} is not of expected type {expected}.")

    return obj
