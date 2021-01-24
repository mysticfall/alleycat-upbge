from typing import Final

from bge.types import SCA_InputEvent
from pytest import fixture
from pytest_mock import MockerFixture

from alleycat.event import EventLoopScheduler
from alleycat.input import KeyInputSource

# noinspection SpellCheckingInspection
ENTERKEY: Final = 7

# noinspection SpellCheckingInspection
ESCKEY: Final = 56


@fixture
def scheduler(mocker: MockerFixture) -> EventLoopScheduler:
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    return EventLoopScheduler()


@fixture
def source(scheduler: EventLoopScheduler) -> KeyInputSource:
    return KeyInputSource(scheduler)


def test_on_key_press(mocker: MockerFixture, source: KeyInputSource, scheduler: EventLoopScheduler):
    keyboard = mocker.patch("bge.logic.keyboard")

    pressed = []

    with source.on_key_press(ENTERKEY).subscribe(pressed.append):
        assert len(pressed) == 0

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent()}
        scheduler.process()

        assert pressed == [ENTERKEY]

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent(), ESCKEY: SCA_InputEvent()}
        scheduler.process()

        assert pressed == [ENTERKEY]


def test_on_key_release(mocker: MockerFixture, source: KeyInputSource, scheduler: EventLoopScheduler):
    keyboard = mocker.patch("bge.logic.keyboard")

    released = []

    with source.on_key_release(ENTERKEY).subscribe(released.append):
        assert len(released) == 0

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent(), ESCKEY: SCA_InputEvent()}
        scheduler.process()

        assert released == []

        keyboard.activeInputs = {ESCKEY: SCA_InputEvent()}
        scheduler.process()

        assert released == [ENTERKEY]

        keyboard.activeInputs = {}
        scheduler.process()

        assert released == [ENTERKEY]


def test_pressed(mocker: MockerFixture, source: KeyInputSource, scheduler: EventLoopScheduler):
    keyboard = mocker.patch("bge.logic.keyboard")

    pressed = []

    with source.observe("pressed").subscribe(pressed.append):
        assert pressed == [set()]

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent()}
        scheduler.process()

        assert len(pressed) == 2
        assert pressed[1:] == [{ENTERKEY}]
        assert source.pressed == {ENTERKEY}

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent(), ESCKEY: SCA_InputEvent()}
        scheduler.process()

        assert len(pressed) == 3
        assert pressed[2:] == [{ENTERKEY, ESCKEY}]
        assert source.pressed == {ENTERKEY, ESCKEY}
