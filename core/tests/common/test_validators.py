import re

from pytest import raises
from returns.maybe import Nothing, Some
from returns.result import Success

from alleycat.common import InvalidTypeError, of_type
from alleycat.common.validators import maybe_type, require_type
from alleycat.test import assert_failure


def test_of_type():
    assert of_type("test", str) == "test"
    assert of_type({"test": 123}, dict) == {"test": 123}

    with raises(InvalidTypeError, match=re.escape("Value 123 is not of expected type 'str' (actual: 'int').")):
        assert of_type(123, str) == 123


def test_maybe_type():
    assert maybe_type("test", str) == Some("test")
    assert maybe_type({"test": 123}, dict) == Some({"test": 123})

    assert maybe_type(123, str) == Nothing
    assert maybe_type("test", dict) == Nothing


def test_require_type():
    assert require_type("test", str) == Success("test")
    assert require_type({"test": 123}, dict) == Success({"test": 123})

    result = require_type(123, str)

    assert_failure(result, InvalidTypeError("Value 123 is not of expected type 'str' (actual: 'int')."))
