from typing import Final
from unittest.mock import PropertyMock

import bge
from pytest import fixture, mark
from pytest_mock import MockerFixture

from alleycat.event import EventLoopScheduler
from alleycat.input import MouseButton, MouseInputSource
from tests.input import InputState, create_event

LEFTMOUSE: Final = 116

MIDDLEMOUSE: Final = 117

RIGHTMOUSE: Final = 118

WHEELUPMOUSE: Final = 120

WHEELDOWNMOUSE: Final = 121

KX_INPUT_NONE: Final = 0
KX_INPUT_JUST_ACTIVATED: Final = 1
KX_INPUT_ACTIVE: Final = 2
KX_INPUT_JUST_RELEASED: Final = 3


@fixture
def scheduler(mocker: MockerFixture) -> EventLoopScheduler:
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    return EventLoopScheduler()


@fixture
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> MouseInputSource:
    events = type(mocker.patch("bge.events"))

    events.LEFTMOUSE = PropertyMock(return_value=LEFTMOUSE)
    events.MIDDLEMOUSE = PropertyMock(return_value=MIDDLEMOUSE)
    events.RIGHTMOUSE = PropertyMock(return_value=RIGHTMOUSE)

    events.WHEELUPMOUSE = PropertyMock(return_value=WHEELUPMOUSE)
    events.WHEELDOWNMOUSE = PropertyMock(return_value=WHEELDOWNMOUSE)

    logic = type(mocker.patch("bge.logic"))

    logic.KX_INPUT_NONE = PropertyMock(return_value=KX_INPUT_NONE)
    logic.KX_INPUT_JUST_ACTIVATED = PropertyMock(return_value=KX_INPUT_JUST_ACTIVATED)
    logic.KX_INPUT_ACTIVE = PropertyMock(return_value=KX_INPUT_ACTIVE)
    logic.KX_INPUT_JUST_RELEASED = PropertyMock(return_value=KX_INPUT_JUST_RELEASED)

    mouse = type(mocker.patch("bge.logic.mouse"))
    mouse.position = (0.5, 0.5)

    return MouseInputSource(scheduler)


def test_buttons(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    buttons = []

    with source.observe("buttons").subscribe(buttons.append):
        assert buttons == [set()]

        mouse.activeInputs = {MouseButton.LEFT.event: create_event(InputState.Active)}

        scheduler.process()

        assert len(buttons) == 2
        assert buttons[1:] == [{MouseButton.LEFT}]

        mouse.activeInputs = {
            MouseButton.LEFT.event: create_event(InputState.Active),
            MouseButton.MIDDLE.event: create_event(InputState.JustActivated)}

        scheduler.process()

        assert len(buttons) == 3
        assert buttons[2:] == [{MouseButton.LEFT, MouseButton.MIDDLE}]

        mouse.activeInputs = {
            MouseButton.LEFT.event: create_event(InputState.Released),
            MouseButton.MIDDLE.event: create_event(InputState.Active),
            MouseButton.RIGHT.event: create_event(InputState.JustActivated)}

        scheduler.process()

        assert len(buttons) == 4
        assert buttons[3:] == [{MouseButton.MIDDLE, MouseButton.RIGHT}]


@mark.parametrize("button", MouseButton)
def test_on_button_press(
        button: MouseButton,
        mocker: MockerFixture,
        source: MouseInputSource,
        scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    pressed = []

    with source.on_button_press(button).subscribe(pressed.append):
        assert pressed == []

        mouse.activeInputs = {button.event: create_event(InputState.JustActivated)}
        scheduler.process()

        assert pressed == [button]

        mouse.activeInputs = {button.event: create_event(InputState.Active)}
        scheduler.process()

        assert pressed == [button]

        mouse.activeInputs = {button.event: create_event(InputState.Released)}
        scheduler.process()

        assert pressed == [button]

        mouse.activeInputs = {button.event: create_event(InputState.JustActivated)}
        scheduler.process()

        assert pressed == [button, button]


@mark.parametrize("button", MouseButton)
def test_on_button_release(
        button: MouseButton,
        mocker: MockerFixture,
        source: MouseInputSource,
        scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    released = []

    with source.on_button_release(button).subscribe(released.append):
        assert released == []

        mouse.activeInputs = {button.event: create_event(InputState.JustActivated)}
        scheduler.process()

        assert released == []

        mouse.activeInputs = {button.event: create_event(InputState.Active)}
        scheduler.process()

        assert released == []

        mouse.activeInputs = {button.event: create_event(InputState.Released)}
        scheduler.process()

        assert released == [button]

        mouse.activeInputs = {}
        scheduler.process()

        assert released == [button]


def test_position(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")
    mouse.position = (0.5, 0.5)

    positions = []

    with source.observe("position").subscribe(positions.append):
        assert positions == [(0.5, 0.5)]

        mouse.position = (0.7, 0.2)
        scheduler.process()

        assert positions == [(0.5, 0.5), (0.7, 0.2)]


def test_on_wheel_move(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    scroll = []

    with source.on_wheel_move.subscribe(scroll.append):
        assert scroll == []

        mouse.activeInputs = {WHEELUPMOUSE: create_event(InputState.Active, values=(0, 1))}
        scheduler.process()

        assert scroll == [1]

        mouse.activeInputs = {WHEELDOWNMOUSE: create_event(InputState.Active, values=(0, -1))}
        scheduler.process()

        assert scroll == [1, -1]


def test_show_mouse(mocker: MockerFixture, source: MouseInputSource):
    method = mocker.spy(bge.render, "showMouse")

    status = []

    with source.observe("show_pointer").subscribe(status.append):
        assert status == [False]
        assert not source.show_pointer

        source.show_pointer = True

        assert status == [False, True]

        method.assert_called_once_with(True)

        source.show_pointer = False

        assert status == [False, True, False]

        method.assert_called_with(False)
