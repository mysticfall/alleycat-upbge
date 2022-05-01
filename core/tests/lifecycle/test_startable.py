from typing import Any, OrderedDict

from pytest import raises
from returns.pipeline import is_successful
from returns.result import Success

from alleycat.lifecycle import AlreadyStartedError, NotStartedError, Startable


def test_startable():
    class TestStartable(Startable):
        do_start_invoked = False

        def _do_start(self) -> None:
            super()._do_start()

            self.do_start_invoked = True

    startable = TestStartable()

    events = []

    startable.on_start.subscribe(events.append)

    assert not startable.started
    assert not startable.do_start_invoked
    assert len(events) == 0

    with raises(NotStartedError):
        startable._check_started()

    startable.start(OrderedDict[str, Any]((("Test Property", 123),)))

    assert startable.started
    assert startable.do_start_invoked
    assert len(events) == 1

    startable._check_started()

    with raises(AlreadyStartedError):
        startable.start(OrderedDict[str, Any](()))

    assert is_successful(startable.start_args)

    args = startable.start_args.unwrap()

    assert args.require("Test Property", int) == Success(123)
