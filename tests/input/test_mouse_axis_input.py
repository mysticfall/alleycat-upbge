from alleycat.reactive import functions as rv
from pytest import approx, fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import Axis2D, MouseAxisInput, MouseInputSource


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
    mouse = mocker.patch("bge.logic.mouse")
    mouse.position = (0.5, 0.5)

    return MouseInputSource(scheduler)


@mark.parametrize("axis", Axis2D)
@mark.parametrize("window_size", (0.5, 0.2))
@mark.parametrize("window_shift", (0.03, 0.01))
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_from_config(
        axis: Axis2D,
        window_size: float,
        window_shift: float,
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: MouseInputSource):
    config = {
        "type": "mouse_axis",
        "axis": axis.name.lower(),
        "window_size": window_size,
        "window_shift": window_shift,
        "sensitivity": sensitivity,
        "dead_zone": dead_zone,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = MouseAxisInput.from_config(source, config)

    assert input
    assert input.axis == axis
    assert input.window_size == window_size
    assert input.window_shift == window_shift
    assert input.sensitivity == sensitivity
    assert input.dead_zone == dead_zone
    assert input.enabled == enabled


def test_from_default_config(source: MouseInputSource):
    config = {
        "type": "mouse_axis",
        "axis": "y"
    }

    # noinspection PyShadowingBuiltins
    input = MouseAxisInput.from_config(source, config)

    assert input
    assert input.axis == Axis2D.Y
    assert input.window_size == 0.0
    assert input.window_shift == 0.0
    assert input.sensitivity == 1.0
    assert input.dead_zone == 0.0
    assert input.enabled


def test_from_config_missing_type(source: MouseInputSource):
    config = {
        "axis": "x"
    }

    with raises(JSONValidationError) as e:
        MouseAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(source: MouseInputSource):
    config = {
        "type": "key_press",
        "axis": "y"
    }

    with raises(JSONValidationError) as e:
        MouseAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'mouse_axis' was expected"


def test_from_config_missing_axis(source: MouseInputSource):
    config = {
        "type": "mouse_axis"
    }

    with raises(JSONValidationError) as e:
        MouseAxisInput.from_config(source, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'axis' is a required property"


@mark.parametrize("axis", Axis2D)
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_input(
        mocker: MockerFixture,
        axis: Axis2D,
        sensitivity: float,
        dead_zone: float,
        enabled: bool,
        source: MouseInputSource,
        scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    positions = ((0.3, 0.6), (0.5, 0.4), (1.0, 0.1))
    values = []

    # noinspection PyShadowingBuiltins
    with MouseAxisInput(axis, source, sensitivity=sensitivity, dead_zone=dead_zone, enabled=enabled) as input:
        rv.observe(input.value).subscribe(values.append)

        assert input.value == 0
        assert values == [0]

        for position in positions:
            mouse.position = position
            scheduler.process()

            if not enabled:
                continue

            value = min(max(-1, (position[axis.value] - 0.5) * 2.0 * sensitivity), 1)

            if abs(value) < dead_zone:
                value = 0

            assert input.value == approx(value)
            assert values[-1] == approx(value)

        if not enabled:
            assert input.value == 0
            assert values == [0]


def test_input_with_pointer_shown(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    values = []

    # noinspection PyShadowingBuiltins
    with MouseAxisInput(Axis2D.X, source) as input:
        rv.observe(input.value).subscribe(values.append)

        assert values == [0.0]

        source.show_pointer = True

        mouse.position = (0.2, 0.3)
        scheduler.process()

        assert values == [0.0]

        source.show_pointer = False

        mouse.position = (0.1, 0.5)
        scheduler.process()

        assert values == [0.0, -0.8]


def test_input_repeat(mocker: MockerFixture, source: MouseInputSource, scheduler: EventLoopScheduler):
    mouse = mocker.patch("bge.logic.mouse")

    values = []

    # noinspection PyShadowingBuiltins
    with MouseAxisInput(Axis2D.Y, source) as input:
        rv.observe(input.value).subscribe(values.append)

        mouse.position = (0.2, 0.3)
        scheduler.process()

        mouse.position = (0.2, 0.3)
        scheduler.process()

        mouse.position = (0.5, 0.5)
        scheduler.process()

        mouse.position = (0.5, 0.5)
        scheduler.process()

        assert values == [0.0, -0.4, -0.4, 0.0, 0.0]


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
    with MouseAxisInput(Axis2D.Y, source, window_size=window_size, window_shift=window_shift) as input:
        mouse.position = (0.5, 0.0)
        scheduler.process()

        while timer.return_value <= window_size:
            timer.return_value += window_shift

            mouse.position = (0.5, 0.0)
            scheduler.process()

        assert input.value == approx(-1.0)

        mouse.position = (0.5, 1.0)

        steps = int(window_size / window_shift)

        for i in range(0, steps):
            timer.return_value += window_shift

            mouse.position = (0.5, 1.0)
            scheduler.process()

            assert input.value == approx((i + 1) / steps * 2.0 - 1.0)

        assert input.value == approx(1.0)
