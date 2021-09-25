from typing import Final
from unittest.mock import PropertyMock

from alleycat.reactive import functions as rv
from pytest import fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import MouseButton, MouseButtonInput, MouseInputSource
from tests.input import InputState, create_event

LEFTMOUSE: Final = 116
MIDDLEMOUSE: Final = 117
RIGHTMOUSE: Final = 118

KX_INPUT_NONE: Final = 0
KX_INPUT_JUST_ACTIVATED: Final = 1
KX_INPUT_ACTIVE: Final = 2
KX_INPUT_JUST_RELEASED: Final = 3


@fixture
def scheduler(mocker: MockerFixture) -> EventLoopScheduler:
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    return EventLoopScheduler()


# noinspection DuplicatedCode
@fixture
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> MouseInputSource:
    events = type(mocker.patch("bge.events"))

    events.LEFTMOUSE = PropertyMock(return_value=LEFTMOUSE)
    events.MIDDLEMOUSE = PropertyMock(return_value=MIDDLEMOUSE)
    events.RIGHTMOUSE = PropertyMock(return_value=RIGHTMOUSE)

    logic = type(mocker.patch("bge.logic"))

    logic.KX_INPUT_NONE = PropertyMock(return_value=KX_INPUT_NONE)
    logic.KX_INPUT_JUST_ACTIVATED = PropertyMock(return_value=KX_INPUT_JUST_ACTIVATED)
    logic.KX_INPUT_ACTIVE = PropertyMock(return_value=KX_INPUT_ACTIVE)
    logic.KX_INPUT_JUST_RELEASED = PropertyMock(return_value=KX_INPUT_JUST_RELEASED)

    return MouseInputSource(scheduler)


@mark.parametrize("button", MouseButton)
@mark.parametrize("repeat", (True, False))
@mark.parametrize("enabled", (True, False))
def test_from_config(button: MouseButton, repeat: bool, enabled: bool, source: MouseInputSource):
    config = {
        "type": "mouse_button",
        "button": button.name,
        "repeat": repeat,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = MouseButtonInput.from_config(source, config)

    assert input
    assert input.button == button
    assert input.repeat == repeat
    assert input.enabled == enabled


def test_from_default_config(source: MouseInputSource):
    config = {
        "type": "mouse_button",
        "button": "LEFT"
    }

    # noinspection PyShadowingBuiltins
    input = MouseButtonInput.from_config(source, config)

    assert input
    assert input.enabled


def test_from_config_missing_type(source: MouseInputSource):
    config = {
        "button": "RIGHT"
    }

    with raises(JSONValidationError) as e:
        MouseButtonInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(source: MouseInputSource):
    config = {
        "type": "key_press",
        "button": "MIDDLE"
    }

    with raises(JSONValidationError) as e:
        MouseButtonInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'mouse_button' was expected"


def test_from_config_missing_button(source: MouseInputSource):
    config = {
        "type": "mouse_button"
    }

    with raises(JSONValidationError) as e:
        MouseButtonInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'button' is a required property"


def test_input(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    pressed = []

    mouse = mocker.patch("bge.logic.mouse")

    # noinspection PyShadowingBuiltins
    with MouseButtonInput(MouseButton.LEFT, source) as input:
        rv.observe(input.value).subscribe(pressed.append)

        assert pressed == [False]
        assert not input.value

        mouse.activeInputs = {LEFTMOUSE: create_event(InputState.JustActivated)}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        mouse.activeInputs = {
            LEFTMOUSE: create_event(InputState.Active), RIGHTMOUSE: create_event(InputState.JustActivated)}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        mouse.activeInputs = {RIGHTMOUSE: create_event(InputState.Active)}
        scheduler.process()

        assert pressed == [False, True, False]
        assert not input.value

        mouse.activeInputs = {}
        scheduler.process()

        assert pressed == [False, True, False]
        assert not input.value


def test_disabled_input(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    pressed = []

    mouse = mocker.patch("bge.logic.mouse")

    # noinspection PyShadowingBuiltins
    with MouseButtonInput(MouseButton.RIGHT, source) as input:
        rv.observe(input.value).subscribe(pressed.append)

        input.enabled = False
        mouse.activeInputs = {RIGHTMOUSE: create_event(InputState.JustActivated)}

        scheduler.process()

        assert pressed == [False]
        assert not input.value

        mouse.activeInputs = {}
        scheduler.process()

        assert pressed == [False]
        assert not input.value

        input.enabled = True
        mouse.activeInputs = {RIGHTMOUSE: create_event(InputState.Active)}

        scheduler.process()

        assert pressed == [False, True]
        assert input.value


@mark.parametrize("repeat", (True, False))
def test_repeat(repeat: bool, mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    pressed = []

    mouse = mocker.patch("bge.logic.mouse")

    # noinspection PyShadowingBuiltins
    with MouseButtonInput(MouseButton.RIGHT, source, repeat=repeat) as input:
        rv.observe(input.value).subscribe(pressed.append)

        mouse.activeInputs = {RIGHTMOUSE: create_event(InputState.JustActivated)}

        scheduler.process()

        mouse.activeInputs = {RIGHTMOUSE: create_event(InputState.Active)}

        scheduler.process()

        mouse.activeInputs = {
            LEFTMOUSE: create_event(InputState.JustActivated), RIGHTMOUSE: create_event(InputState.Active)}

        scheduler.process()

        mouse.activeInputs = {
            LEFTMOUSE: create_event(InputState.Active), RIGHTMOUSE: create_event(InputState.Released)}

        scheduler.process()

        mouse.activeInputs = {LEFTMOUSE: create_event(InputState.Active)}

        scheduler.process()

        if repeat:
            assert pressed == [False, True, True, True, False, False]
        else:
            assert pressed == [False, True, False]
