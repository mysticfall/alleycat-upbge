from typing import Final, Set
from unittest.mock import PropertyMock

from alleycat.reactive import functions as rv
from pytest import approx, fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import MouseInputSource, MouseWheelInput
from tests.input import InputState, create_event

WHEELUPMOUSE: Final = 120
WHEELDOWNMOUSE: Final = 121

KX_INPUT_NONE: Final = 0
KX_INPUT_JUST_ACTIVATED: Final = 1
KX_INPUT_ACTIVE: Final = 2
KX_INPUT_JUST_RELEASED: Final = 3


@fixture
def timer(mocker: MockerFixture):
    timer = mocker.patch("bge.logic.getFrameTime")
    timer.return_value = 0.

    return timer


@fixture
def scheduler(timer) -> EventLoopScheduler:
    return EventLoopScheduler()


@fixture
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> MouseInputSource:
    events = type(mocker.patch("bge.events"))

    events.WHEELUPMOUSE = PropertyMock(return_value=WHEELUPMOUSE)
    events.WHEELDOWNMOUSE = PropertyMock(return_value=WHEELDOWNMOUSE)

    logic = type(mocker.patch("bge.logic"))

    logic.KX_INPUT_NONE = PropertyMock(return_value=KX_INPUT_NONE)
    logic.KX_INPUT_JUST_ACTIVATED = PropertyMock(return_value=KX_INPUT_JUST_ACTIVATED)
    logic.KX_INPUT_ACTIVE = PropertyMock(return_value=KX_INPUT_ACTIVE)
    logic.KX_INPUT_JUST_RELEASED = PropertyMock(return_value=KX_INPUT_JUST_RELEASED)

    return MouseInputSource(scheduler)


@mark.parametrize("window_size", (0.5, 0.2))
@mark.parametrize("window_shift", (0.03, 0.01))
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_from_config(
        window_size: float,
        window_shift: float,
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: MouseInputSource):
    config = {
        "type": "mouse_wheel",
        "window_size": window_size,
        "window_shift": window_shift,
        "sensitivity": sensitivity,
        "dead_zone": dead_zone,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = MouseWheelInput.from_config(source, config)

    assert input
    assert input.window_size == window_size
    assert input.window_shift == window_shift
    assert input.sensitivity == sensitivity
    assert input.dead_zone == dead_zone
    assert input.enabled == enabled


def test_from_default_config(source: MouseInputSource):
    config = {
        "type": "mouse_wheel"
    }

    # noinspection PyShadowingBuiltins
    input = MouseWheelInput.from_config(source, config)

    assert input
    assert input.window_size == 0.1
    assert input.window_shift == 0.01
    assert input.sensitivity == 1.0
    assert input.dead_zone == 0.0
    assert input.enabled


def test_from_config_missing_type(source: MouseInputSource):
    config = {
        "enabled": True
    }

    with raises(JSONValidationError) as e:
        MouseWheelInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(source: MouseInputSource):
    config = {
        "type": "key_press"
    }

    with raises(JSONValidationError) as e:
        MouseWheelInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'mouse_wheel' was expected"


@mark.parametrize("inputs", ({}, {WHEELUPMOUSE}, {WHEELDOWNMOUSE}))
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_input(
        mocker: MockerFixture,
        inputs: Set[int],
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: MouseInputSource,
        scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    values = []

    # noinspection PyShadowingBuiltins
    with MouseWheelInput(
            source,
            window_shift=0,
            window_size=0,
            sensitivity=sensitivity,
            dead_zone=dead_zone,
            enabled=enabled) as input:

        rv.observe(input.value).subscribe(values.append)

        assert input.value == 0
        assert values == [0]

        if not enabled:
            return

        def get_value():
            base = 0

            if WHEELUPMOUSE in mouse.activeInputs:
                base += mouse.activeInputs[WHEELUPMOUSE].values[-1]

            if WHEELDOWNMOUSE in mouse.activeInputs:
                base += mouse.activeInputs[WHEELDOWNMOUSE].values[-1]

            value = min(max(-1.0, base * sensitivity), 1.0)

            if abs(value) < dead_zone:
                value = 0

            return value

        mouse.activeInputs = dict(map(lambda i: (i, create_event(InputState.JustActivated, (0, 1))), inputs))

        scheduler.process()

        assert input.value == approx(get_value())
        assert values[-1] == approx(get_value())


@mark.parametrize("window_size", (0.1, 0.2))
@mark.parametrize("window_shift", (0.02, 0.05))
def test_input_interpolation(
        timer,
        window_size: float,
        window_shift: float,
        mocker: MockerFixture,
        source: MouseInputSource,
        scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    # noinspection PyShadowingBuiltins
    with MouseWheelInput(source, window_size=window_size, window_shift=window_shift) as input:
        mouse.activeInputs = {}
        scheduler.process()

        while timer.return_value <= window_size:
            timer.return_value += window_shift

            mouse.activeInputs = {WHEELDOWNMOUSE: create_event(InputState.JustActivated, (0, -1))}
            scheduler.process()

        assert input.value == approx(-1.0)

        mouse.activeInputs = {WHEELUPMOUSE: create_event(InputState.JustActivated, (0, 1))}

        steps = int(window_size / window_shift)

        for i in range(0, steps):
            timer.return_value += window_shift

            mouse.activeInputs = {WHEELUPMOUSE: create_event(InputState.JustActivated, (0, 1))}
            scheduler.process()

            assert input.value == approx((i + 1) / steps * 2.0 - 1.0)

        assert input.value == approx(1.0)
