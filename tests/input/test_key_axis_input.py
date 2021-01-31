from typing import Final, Tuple
from unittest.mock import PropertyMock

from bge.types import SCA_InputEvent
from pytest import approx, fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import KeyAxisInput, KeyInputSource

W: Final = 45
S: Final = 41
A: Final = 23
D: Final = 26


@fixture
def timer(mocker: MockerFixture):
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    return timer


@fixture
def scheduler(timer) -> EventLoopScheduler:
    return EventLoopScheduler()


@fixture
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> KeyInputSource:
    events = type(mocker.patch("bge.events"))

    events.WKEY = PropertyMock(return_value=W)
    events.SKEY = PropertyMock(return_value=S)
    events.AKEY = PropertyMock(return_value=A)
    events.DKEY = PropertyMock(return_value=D)

    return KeyInputSource(scheduler)


@mark.parametrize("keys", ((W, S), (A, D)))
@mark.parametrize("window_size", (0.5, 0.2))
@mark.parametrize("window_shift", (0.03, 0.01))
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_from_config(
        keys: Tuple[int, int],
        window_size: float,
        window_shift: float,
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: KeyInputSource):
    config = {
        "type": "key_axis",
        "positive_key": keys[0],
        "negative_key": keys[1],
        "window_size": window_size,
        "window_shift": window_shift,
        "sensitivity": sensitivity,
        "dead_zone": dead_zone,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = KeyAxisInput.from_config(source, config)

    assert input
    assert input.positive_key == keys[0]
    assert input.negative_key == keys[1]
    assert input.window_size == window_size
    assert input.window_shift == window_shift
    assert input.sensitivity == sensitivity
    assert input.dead_zone == dead_zone
    assert input.enabled == enabled


def test_from_config_with_key_names(source: KeyInputSource):
    config = {
        "type": "key_axis",
        "positive_key": "WKEY",
        "negative_key": "SKEY"
    }

    # noinspection PyShadowingBuiltins
    input = KeyAxisInput.from_config(source, config)

    assert input
    assert input.positive_key == W
    assert input.negative_key == S


def test_from_default_config(source: KeyInputSource):
    config = {
        "type": "key_axis",
        "positive_key": W,
        "negative_key": S
    }

    # noinspection PyShadowingBuiltins
    input = KeyAxisInput.from_config(source, config)

    assert input
    assert input.positive_key == W
    assert input.negative_key == S
    assert input.window_size == 0.1
    assert input.window_shift == 0.01
    assert input.sensitivity == 1.0
    assert input.dead_zone == 0.0
    assert input.enabled


def test_from_config_missing_type(source: KeyInputSource):
    config = {
        "positive_key": W,
        "negative_key": S
    }

    with raises(JSONValidationError) as e:
        KeyAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(source: KeyInputSource):
    config = {
        "type": "key_press",
        "positive_key": W,
        "negative_key": S
    }

    with raises(JSONValidationError) as e:
        KeyAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'key_axis' was expected"


def test_from_config_positive_key(source: KeyInputSource):
    config = {
        "type": "key_axis",
        "negative_key": S
    }

    with raises(JSONValidationError) as e:
        KeyAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'positive_key' is a required property"


def test_from_config_negative_key(source: KeyInputSource):
    config = {
        "type": "key_axis",
        "positive_key": W
    }

    with raises(JSONValidationError) as e:
        KeyAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'negative_key' is a required property"


@mark.parametrize("keys", ((W, S), (A, D)))
@mark.parametrize("pressed", ((False, False), (True, False), (False, True), (True, True)))
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_input(
        mocker: MockerFixture,
        keys: Tuple[int, int],
        pressed: Tuple[bool, bool],
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: KeyInputSource,
        scheduler: EventLoopScheduler):
    keyboard = mocker.patch("bge.logic.keyboard")

    values = []

    # noinspection PyShadowingBuiltins
    with KeyAxisInput(keys[0], keys[1], source, 0, 0, sensitivity, dead_zone, enabled) as input:
        input.observe("value").subscribe(values.append)

        assert input.value == 0
        assert values == [0]

        keyboard.activeInputs = dict()

        if pressed[0]:
            keyboard.activeInputs[keys[0]] = SCA_InputEvent()

        if pressed[1]:
            keyboard.activeInputs[keys[1]] = SCA_InputEvent()

        scheduler.process()

        if enabled:
            value = ((1 if pressed[0] else 0) - (1 if pressed[1] else 0)) * sensitivity

            if abs(value) < dead_zone:
                value = 0

            assert input.value == value
            assert values[-1] == value
        else:
            assert input.value == 0
            assert values == [0]


@mark.parametrize("window_size", (0.1, 0.2))
@mark.parametrize("window_shift", (0.02, 0.05))
def test_input_interpolation(
        timer,
        window_size: float,
        window_shift: float,
        mocker: MockerFixture,
        source: KeyInputSource,
        scheduler: EventLoopScheduler):
    keyboard = mocker.patch("bge.logic.keyboard")

    # noinspection PyShadowingBuiltins
    with KeyAxisInput(W, S, source, window_size, window_shift) as input:
        keyboard.activeInputs = dict()

        scheduler.process()

        while timer.return_value < window_size:
            timer.return_value += window_shift
            scheduler.process()

        keyboard.activeInputs = {W: SCA_InputEvent()}

        steps = int(window_size / window_shift)

        for i in range(0, steps):
            timer.return_value += window_shift
            scheduler.process()

            assert input.value == approx((i + 1) / steps)

        assert input.value == 1.0
