from typing import cast

from pytest import raises
from returns.maybe import Nothing, Some
from returns.result import Result, Success

from alleycat.common import InvalidTypeError, of_type
from alleycat.common.validators import maybe_type, require_type


def test_of_type():
    assert of_type("test", str) == "test"
    assert of_type({"test": 123}, dict) == {"test": 123}

    with raises(InvalidTypeError) as e:
        assert of_type(123, str) == 123

    assert e.value.args[0] == "Value 123 is not of expected type <class 'str'>."


def test_maybe_type():
    assert maybe_type("test", str) == Some("test")
    assert maybe_type({"test": 123}, dict) == Some({"test": 123})

    assert maybe_type(123, str) == Nothing
    assert maybe_type("test", dict) == Nothing


def test_require_type():
    assert require_type("test", str) == Success("test")
    assert require_type({"test": 123}, dict) == Success({"test": 123})

    result = require_type(123, str)
    error = result.swap().unwrap()

    assert type(result) == Result.failure_type
    assert type(error) == InvalidTypeError
    assert cast(InvalidTypeError, error).args[0] == "Value 123 is not of expected type <class 'str'>."
