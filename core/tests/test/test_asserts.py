from pytest import raises
from returns.result import Failure, Success

from alleycat.test import assert_failure, assert_success


def test_assert_success():
    assert_success(Success(123), 123)

    with raises(AssertionError):
        assert_success(Success(123), 567)

    with raises(AssertionError):
        assert_success(Success(123), "ABC")

    with raises(AssertionError):
        assert_success(Failure(123), 123)


def test_assert_failure():
    assert_failure(Failure(123), 123)

    assert_failure(Failure(ValueError("test")), ValueError("test"))

    with raises(AssertionError):
        assert_failure(Failure(123), 567)

    with raises(AssertionError):
        assert_failure(Failure(123), "ABC")

    with raises(AssertionError):
        assert_failure(Failure(123), "ABC")

    with raises(AssertionError):
        assert_failure(Success(123), 123)

    with raises(AssertionError):
        assert_failure(Failure(ValueError("ABC")), ValueError("DEF"))

    with raises(AssertionError):
        assert_failure(Failure(ValueError("ABC")), IOError("ABC"))
