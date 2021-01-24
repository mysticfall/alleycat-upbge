from typing import Final
from unittest.mock import PropertyMock

from bge.types import SCA_InputEvent
from pytest import fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import KeyInputSource, KeyPressInput

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
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> KeyInputSource:
    events = type(mocker.patch("bge.events"))

    events.ENTERKEY = PropertyMock(return_value=ENTERKEY)
    events.ESCKEY = PropertyMock(return_value=ESCKEY)

    return KeyInputSource(scheduler)


@mark.parametrize("keycode", (ESCKEY, ENTERKEY))
@mark.parametrize("enabled", (True, False))
def test_from_config(keycode: int, enabled: bool, source: KeyInputSource):
    config = {
        "type": "key_press",
        "key": keycode,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = KeyPressInput.from_config(source, config)

    assert input
    assert input.keycode == keycode
    assert input.enabled == enabled


def test_from_default_config(source: KeyInputSource):
    config = {
        "type": "key_press",
        "key": ESCKEY
    }

    # noinspection PyShadowingBuiltins
    input = KeyPressInput.from_config(source, config)

    assert input
    assert input.enabled


def test_from_config_with_key_name(source: KeyInputSource):
    config = {
        "type": "key_press",
        "key": "ESCKEY"
    }

    # noinspection PyShadowingBuiltins
    input = KeyPressInput.from_config(source, config)

    assert input
    assert input.keycode == ESCKEY


def test_from_config_missing_type(source: KeyInputSource):
    config = {
        "key": "ESCKEY"
    }

    with raises(JSONValidationError) as e:
        KeyPressInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(source: KeyInputSource):
    config = {
        "type": "mouse_button",
        "key": "ESCKEY"
    }

    with raises(JSONValidationError) as e:
        KeyPressInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'key_press' was expected"


def test_from_config_missing_keycode(source: KeyInputSource):
    config = {
        "type": "key_press"
    }

    with raises(JSONValidationError) as e:
        KeyPressInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'key' is a required property"


def test_from_config_enabled(source: KeyInputSource):
    config = {
        "type": "key_press",
        "key": ESCKEY,
        "enabled": True
    }

    # noinspection PyShadowingBuiltins
    input = KeyPressInput.from_config(source, config)

    assert input
    assert input.enabled


def test_from_config_disabled(source: KeyInputSource):
    config = {
        "type": "key_press",
        "key": ESCKEY,
        "enabled": False
    }

    # noinspection PyShadowingBuiltins
    input = KeyPressInput.from_config(source, config)

    assert input
    assert not input.enabled


def test_input(mocker: MockerFixture, source: KeyInputSource, scheduler: EventLoopScheduler):
    pressed = []

    keyboard = mocker.patch("bge.logic.keyboard")

    # noinspection PyShadowingBuiltins
    with KeyPressInput(ESCKEY, source) as input:
        input.observe("value").subscribe(pressed.append)

        assert pressed == [False]
        assert not input.value

        keyboard.activeInputs = {ESCKEY: SCA_InputEvent()}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        keyboard.activeInputs = {ESCKEY: SCA_InputEvent(), ENTERKEY: SCA_InputEvent()}
        scheduler.process()

        assert pressed == [False, True]
        assert input.value

        keyboard.activeInputs = {ENTERKEY: SCA_InputEvent()}
        scheduler.process()

        assert pressed == [False, True, False]
        assert not input.value

        keyboard.activeInputs = {}
        scheduler.process()

        assert pressed == [False, True, False]
        assert not input.value


def test_disabled_input(mocker: MockerFixture, source: KeyInputSource, scheduler: EventLoopScheduler):
    pressed = []

    keyboard = mocker.patch("bge.logic.keyboard")

    # noinspection PyShadowingBuiltins
    with KeyPressInput(ESCKEY, source) as input:
        input.observe("value").subscribe(pressed.append)

        input.enabled = False
        keyboard.activeInputs = {ESCKEY: SCA_InputEvent()}

        scheduler.process()

        assert pressed == [False]
        assert not input.value

        keyboard.activeInputs = {}
        scheduler.process()

        assert pressed == [False]
        assert not input.value

        input.enabled = True
        keyboard.activeInputs = {ESCKEY: SCA_InputEvent()}

        scheduler.process()

        assert pressed == [False, True]
        assert input.value
