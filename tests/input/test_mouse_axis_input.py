from alleycat.reactive import functions as rv
from pytest import approx, fixture, mark, raises
from pytest_mock import MockerFixture
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import Axis2D, MouseAxisInput, MouseInputSource


@fixture
def scheduler(mocker: MockerFixture) -> EventLoopScheduler:
    timer = mocker.patch(f"bge.logic.getFrameTime")
    timer.return_value = 0.

    return EventLoopScheduler()


@fixture
def source(mocker: MockerFixture, scheduler: EventLoopScheduler) -> MouseInputSource:
    mouse = mocker.patch("bge.logic.mouse")
    mouse.position = (0.5, 0.5)

    return MouseInputSource(scheduler)


@mark.parametrize("axis", Axis2D)
@mark.parametrize("sensitivity", (0.4, 0.9))
@mark.parametrize("dead_zone", (0.1, 0.2))
@mark.parametrize("enabled", (True, False))
def test_from_config(axis: Axis2D, sensitivity: float, dead_zone: float, enabled: bool, source: MouseInputSource):
    config = {
        "type": "mouse_axis",
        "axis": axis.name.lower(),
        "sensitivity": sensitivity,
        "dead_zone": dead_zone,
        "enabled": enabled
    }

    # noinspection PyShadowingBuiltins
    input = MouseAxisInput.from_config(source, config)

    assert input
    assert input.axis == axis
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
    with MouseAxisInput(axis, source, sensitivity, dead_zone, enabled) as input:
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
