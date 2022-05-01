from typing import Any, OrderedDict

from pytest import raises
from returns.pipeline import is_successful
from returns.result import ResultE, Success

from alleycat.common import MapReader
from alleycat.lifecycle import AlreadyStartedError, NotStartedError, Startable


def test_startable():
    class TestStartable(Startable):

        def _do_start(self, args: MapReader) -> ResultE[MapReader]:
            def multiply(d: MapReader):
                items = map(lambda t: (t[0], t[1] * 2), d.items())

                return MapReader(dict(items))

            return super()._do_start(args).map(multiply)

    startable = TestStartable()

    events = []
    errors = []

    startable.on_start.subscribe(events.append, on_error=errors.append)

    assert not startable.started
    assert len(events) == 0
    assert len(errors) == 0

    with raises(NotStartedError):
        startable._check_started()

    startable.start(OrderedDict[str, Any]((("Test Property", 123),)))

    assert startable.started
    assert len(events) == 1
    assert len(errors) == 0

    startable._check_started()

    with raises(AlreadyStartedError):
        startable.start(OrderedDict[str, Any](()))

    assert is_successful(startable.start_args)

    start_args = startable.start_args.unwrap()

    assert start_args.require("Test Property", int) == Success(246)


def test_start_failure():
    expected_error = BaseException("Something bad happened!")

    class FaultyStartable(Startable):

        def _do_start(self, args: MapReader) -> ResultE[MapReader]:
            return ResultE[MapReader].from_failure(expected_error)

    startable = FaultyStartable()

    events = []
    errors = []

    startable.on_start.subscribe(events.append, on_error=errors.append)

    assert not startable.started
    assert len(events) == 0
    assert len(errors) == 0

    with raises(NotStartedError):
        startable._check_started()

    startable.start(OrderedDict[str, Any]((("Test Property", 123),)))

    assert startable.started
    assert len(events) == 0
    assert errors == [expected_error]

    startable._check_started()

    assert not is_successful(startable.start_args)

    actual_error = startable.start_args.failure()

    assert actual_error == expected_error
