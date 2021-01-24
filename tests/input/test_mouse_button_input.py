from typing import Final
from unittest.mock import PropertyMock

from pytest import fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import MouseButton, MouseButtonInput, MouseInputSource
from tests.input import create_event

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
@mark.parametrize("enabled", (True, False))
def test_from_config(button: MouseButton, enabled: bool, source: MouseInputSource):
    config = {
        "type": "mouse_button",
        "button": button.name,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = MouseButtonInput.from_config(source, config)

    assert input
    assert input.button == button
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
        input.observe("value").subscribe(pressed.append)

        assert pressed == [False]
        assert not input.value

        mouse.activeInputs = {LEFTMOUSE: create_event(status=[0, 1])}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        mouse.activeInputs = {LEFTMOUSE: create_event(status=[1, 1]), RIGHTMOUSE: create_event(status=[0, 1])}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        mouse.activeInputs = {RIGHTMOUSE: create_event(status=[1, 1])}
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
        input.observe("value").subscribe(pressed.append)

        input.enabled = False
        mouse.activeInputs = {RIGHTMOUSE: create_event(status=[0, 1])}

        scheduler.process()

        assert pressed == [False]
        assert not input.value

        mouse.activeInputs = {}
        scheduler.process()

        assert pressed == [False]
        assert not input.value

        input.enabled = True
        mouse.activeInputs = {RIGHTMOUSE: create_event(status=[1, 1])}

        scheduler.process()

        assert pressed == [False, True]
        assert input.value
