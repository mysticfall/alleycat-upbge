from collections import OrderedDict

from _pytest.fixtures import fixture
from bge.events import LEFTMOUSE, MIDDLEMOUSE
from bge.logic import KX_INPUT_ACTIVE, KX_INPUT_JUST_RELEASED
from bge.types import SCA_PythonMouse
from returns.result import Result

from alleycat.common import Point2D
from alleycat.core import bootstrap
from alleycat.input import MouseButton, MouseDownEvent, MouseInputSource, MouseMoveEvent, MouseState, MouseUpEvent
from alleycat.lifecycle import RESULT_DISPOSED, RESULT_NOT_STARTED
from alleycat.test.mock_bge import SCA_InputEvent


def setup():
    bootstrap._initialised = True


def teardown():
    bootstrap._initialised = False


@fixture
def mouse() -> SCA_PythonMouse:
    from bge.logic import mouse

    mouse.position = (0.5, 0.5)
    mouse.activeInputs = {}

    return mouse


def test_mouse_state(mouse: SCA_PythonMouse):
    comp = MouseInputSource()

    def state_of(x, y, *args):
        return Result.from_value(MouseState(Point2D(x, y), set(args)))

    assert comp.state == RESULT_NOT_STARTED

    comp.start(OrderedDict(()))

    assert comp.state == state_of(0.5, 0.5)

    comp.update()

    assert comp.state == state_of(0.5, 0.5)

    mouse.position = (0.8, 0.3)
    mouse.activeInputs = {
        LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,)),
        MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
    }

    assert comp.state == state_of(0.5, 0.5)

    comp.update()

    assert comp.state == state_of(0.8, 0.3, MouseButton.LEFT, MouseButton.MIDDLE)

    mouse.activeInputs = {
        LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,)),
        MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_JUST_RELEASED,))
    }

    comp.update()

    assert comp.state == state_of(0.8, 0.3, MouseButton.LEFT)

    comp.dispose()

    assert comp.state == RESULT_DISPOSED


def test_on_mouse_move(mouse: SCA_PythonMouse):
    comp = MouseInputSource()

    data = {
        "events": [],
        "errors": [],
        "completed": False
    }

    def on_completed():
        data["completed"] = True

    def moved_to(x, y):
        return MouseMoveEvent(comp, MouseState(Point2D(x, y), set()))

    with comp.on_mouse_move.subscribe(
            on_next=data["events"].append,
            on_error=data["errors"].append,
            on_completed=on_completed):
        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        comp.start(OrderedDict(()))

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [moved_to(0.5, 0.5)]

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [moved_to(0.5, 0.5)]

        mouse.position = (0.8, 0.3)

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [moved_to(0.5, 0.5), moved_to(0.8, 0.3)]

        comp.dispose()

        assert data["completed"]
        assert data["errors"] == []
        assert data["events"] == [moved_to(0.5, 0.5), moved_to(0.8, 0.3)]


def test_on_mouse_down(mouse: SCA_PythonMouse):
    comp = MouseInputSource()

    data = {
        "events": [],
        "errors": [],
        "completed": False
    }

    def on_completed():
        data["completed"] = True

    def clicked_at(x, y, button, buttons):
        return MouseDownEvent(comp, MouseState(Point2D(x, y), buttons), button)

    with comp.on_mouse_down.subscribe(
            on_next=data["events"].append,
            on_error=data["errors"].append,
            on_completed=on_completed):
        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        comp.start(OrderedDict(()))

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, {MouseButton.LEFT})
        ]

        mouse.position = (0.2, 0.9)

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, {MouseButton.LEFT})
        ]

        mouse.position = (0.4, 0.3)
        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,)),
            MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, {MouseButton.LEFT}),
            clicked_at(0.4, 0.3, MouseButton.MIDDLE, {MouseButton.LEFT, MouseButton.MIDDLE})
        ]

        mouse.position = (0.2, 0.5)
        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_JUST_RELEASED,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, {MouseButton.LEFT}),
            clicked_at(0.4, 0.3, MouseButton.MIDDLE, {MouseButton.LEFT, MouseButton.MIDDLE})
        ]

        comp.dispose()

        assert data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, {MouseButton.LEFT}),
            clicked_at(0.4, 0.3, MouseButton.MIDDLE, {MouseButton.LEFT, MouseButton.MIDDLE})
        ]


def test_on_mouse_up(mouse: SCA_PythonMouse):
    comp = MouseInputSource()

    data = {
        "events": [],
        "errors": [],
        "completed": False
    }

    def on_completed():
        data["completed"] = True

    def clicked_at(x, y, button, buttons):
        return MouseUpEvent(comp, MouseState(Point2D(x, y), buttons), button)

    with comp.on_mouse_up.subscribe(
            on_next=data["events"].append,
            on_error=data["errors"].append,
            on_completed=on_completed):
        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        comp.start(OrderedDict(()))

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == []

        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_JUST_RELEASED,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, set())
        ]

        mouse.position = (0.4, 0.3)
        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,)),
            MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, set())
        ]

        mouse.position = (0.6, 0.3)
        mouse.activeInputs = {
            MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, set()),
            clicked_at(0.6, 0.3, MouseButton.LEFT, {MouseButton.MIDDLE})
        ]

        mouse.position = (0.2, 0.2)
        mouse.activeInputs = {
            LEFTMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,)),
            MIDDLEMOUSE: SCA_InputEvent((KX_INPUT_ACTIVE,))
        }

        comp.update()

        assert not data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, set()),
            clicked_at(0.6, 0.3, MouseButton.LEFT, {MouseButton.MIDDLE})
        ]

        comp.dispose()

        assert data["completed"]
        assert data["errors"] == []
        assert data["events"] == [
            clicked_at(0.5, 0.5, MouseButton.LEFT, set()),
            clicked_at(0.6, 0.3, MouseButton.LEFT, {MouseButton.MIDDLE})
        ]
