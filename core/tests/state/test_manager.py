from collections import OrderedDict

from returns.result import Result, ResultE, Success

from alleycat.core import BaseObject, bootstrap
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED
from alleycat.state import StateManager


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


def test_state():
    input_text: str

    class LetterCounter(StateManager[int], BaseObject):

        @property
        def init_state(self) -> ResultE[int]:
            return Result.from_value(0)

        def next_state(self, state: int) -> ResultE[int]:
            return Result.from_value(state + len(input_text))

    counter = LetterCounter()

    assert counter.state == RESULT_NOT_STARTED

    counter.start(OrderedDict(()))

    assert counter.state == Success(0)

    input_text = "abc"
    counter.update()

    assert counter.state == Success(3)

    input_text = "de"

    counter.update()

    assert counter.state == Success(5)

    counter.dispose()

    assert counter.state == RESULT_DISPOSED


def test_on_state_change():
    input_text: str

    class LetterCounter(StateManager[int], BaseObject):

        @property
        def init_state(self) -> ResultE[int]:
            return Result.from_value(0)

        def next_state(self, state: int) -> ResultE[int]:
            return Result.from_value(state + len(input_text))

    counter = LetterCounter()

    data = {
        "state": [],
        "errors": [],
        "completed": False
    }

    def on_completed():
        data["completed"] = True

    counter.on_state_change.subscribe(
        on_next=data["state"].append,
        on_error=data["errors"].append,
        on_completed=on_completed
    )

    assert not data["completed"]
    assert data["errors"] == []
    assert data["state"] == []

    counter.start(OrderedDict(()))

    assert not data["completed"]
    assert data["errors"] == []
    assert data["state"] == []

    input_text = "abc"
    counter.update()

    assert not data["completed"]
    assert data["errors"] == []
    assert data["state"] == [3]

    input_text = "de"

    counter.update()

    assert not data["completed"]
    assert data["errors"] == []
    assert data["state"] == [3, 5]

    counter.dispose()

    assert data["completed"]
    assert data["errors"] == []
    assert data["state"] == [3, 5]
