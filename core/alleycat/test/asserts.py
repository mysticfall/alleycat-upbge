from typing import Any

from returns.pipeline import is_successful
from returns.result import Result


def assert_success(actual: Result[..., ...], expected: Any) -> None:
    assert actual == Result.from_value(expected)


def assert_failure(actual: Result[..., ...], expected: Any) -> None:
    if isinstance(expected, Exception):
        if is_successful(actual):
            raise AssertionError(f"Expected a failure but got {actual}.")

        failure = actual.failure()

        if isinstance(failure, Exception):
            assert failure.__class__ == expected.__class__ and failure.args == expected.args, \
                f"Expected f{expected} but got {actual}."
        else:
            raise AssertionError(f"Expected f{expected} but got {actual}.")
    else:
        assert actual == Result.from_failure(expected)
