from typing import cast

from pytest import fixture

from alleycat.ui import Bounds, Component, Context, DragEndEvent, DragEvent, DragLeaveEvent, DragOverEvent, \
    DragStartEvent, FakeMouseInput, MouseButton, MouseDownEvent, MouseInput, MouseMoveEvent, MouseOutEvent, \
    MouseOverEvent, \
    MouseUpEvent, Point, \
    Window
from tests.ui import UI


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def mouse(context: Context) -> FakeMouseInput:
    return cast(FakeMouseInput, MouseInput.input(context))


@fixture
def component(context: Context) -> Component:
    component = Component(context)
    component.bounds = Bounds(10, 10, 20, 20)

    return component


@fixture
def window(component: Component, context: Context) -> Window:
    window = Window(context)
    window.bounds = Bounds(20, 20, 60, 60)

    window.add(component)

    return window


def test_buttons(mouse: FakeMouseInput):
    assert mouse.buttons == 0

    assert not mouse.pressed(MouseButton.LEFT)
    assert not mouse.pressed(MouseButton.MIDDLE)
    assert not mouse.pressed(MouseButton.RIGHT)

    mouse.press(MouseButton.LEFT)

    assert mouse.pressed(MouseButton.LEFT)
    assert not mouse.pressed(MouseButton.MIDDLE)
    assert not mouse.pressed(MouseButton.RIGHT)

    mouse.press(MouseButton.RIGHT)

    assert mouse.pressed(MouseButton.LEFT)
    assert not mouse.pressed(MouseButton.MIDDLE)
    assert mouse.pressed(MouseButton.RIGHT)

    mouse.release(MouseButton.RIGHT)

    assert mouse.pressed(MouseButton.LEFT)
    assert not mouse.pressed(MouseButton.MIDDLE)
    assert not mouse.pressed(MouseButton.RIGHT)


# noinspection DuplicatedCode
def test_mouse_move(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_mouse_move.subscribe(events.append)
    window.on_mouse_move.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    assert events == []
    assert parent_events == [MouseMoveEvent(window, Point(20, 20))]

    mouse.move_to(Point(30, 30))

    assert events == [MouseMoveEvent(component, Point(30, 30))]
    assert parent_events == [MouseMoveEvent(window, Point(20, 20)), MouseMoveEvent(window, Point(30, 30))]


# noinspection DuplicatedCode
def test_mouse_down(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_mouse_down.subscribe(events.append)
    window.on_mouse_down.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    mouse.click(MouseButton.LEFT)

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    mouse.press(MouseButton.LEFT)
    mouse.click(MouseButton.RIGHT)

    assert events == []

    assert parent_events == [
        MouseDownEvent(window, Point(20, 20), MouseButton.LEFT),
        MouseDownEvent(window, Point(20, 20), MouseButton.RIGHT)
    ]

    mouse.release(MouseButton.LEFT)

    mouse.move_to(Point(30, 30))

    mouse.click(MouseButton.MIDDLE)
    mouse.click(MouseButton.LEFT)

    assert events == [
        MouseDownEvent(component, Point(30, 30), MouseButton.MIDDLE),
        MouseDownEvent(component, Point(30, 30), MouseButton.LEFT)
    ]

    assert parent_events[2:] == [
        MouseDownEvent(window, Point(30, 30), MouseButton.MIDDLE),
        MouseDownEvent(window, Point(30, 30), MouseButton.LEFT)
    ]


# noinspection DuplicatedCode
def test_mouse_up(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_mouse_up.subscribe(events.append)
    window.on_mouse_up.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    mouse.click(MouseButton.LEFT)

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    mouse.press(MouseButton.LEFT)
    mouse.click(MouseButton.RIGHT)

    assert events == []
    assert parent_events == [MouseUpEvent(window, Point(20, 20), MouseButton.RIGHT)]

    mouse.move_to(Point(30, 30))

    mouse.release(MouseButton.LEFT)

    mouse.click(MouseButton.MIDDLE)
    mouse.click(MouseButton.LEFT)

    assert events == [
        MouseUpEvent(component, Point(30, 30), MouseButton.LEFT),
        MouseUpEvent(component, Point(30, 30), MouseButton.MIDDLE),
        MouseUpEvent(component, Point(30, 30), MouseButton.LEFT)
    ]

    assert parent_events[1:] == [
        MouseUpEvent(window, Point(30, 30), MouseButton.LEFT),
        MouseUpEvent(window, Point(30, 30), MouseButton.MIDDLE),
        MouseUpEvent(window, Point(30, 30), MouseButton.LEFT)
    ]


# noinspection DuplicatedCode
def test_mouse_over(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_mouse_over.subscribe(events.append)
    window.on_mouse_over.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    assert events == []
    assert parent_events == [MouseOverEvent(window, Point(20, 20))]

    mouse.move_to(Point(25, 25))

    assert events == []
    assert parent_events == [MouseOverEvent(window, Point(20, 20))]

    mouse.move_to(Point(30, 30))
    mouse.move_to(Point(40, 40))

    assert events == [MouseOverEvent(component, Point(30, 30))]
    assert parent_events == [MouseOverEvent(window, Point(20, 20))]

    mouse.move_to(Point(20, 20))
    mouse.move_to(Point(40, 40))

    assert events == [MouseOverEvent(component, Point(30, 30)), MouseOverEvent(component, Point(40, 40))]
    assert parent_events == [MouseOverEvent(window, Point(20, 20))]


# noinspection DuplicatedCode
def test_mouse_out(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_mouse_out.subscribe(events.append)
    window.on_mouse_out.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(10, 10))

    assert events == []
    assert parent_events == [MouseOutEvent(window, Point(10, 10))]

    mouse.move_to(Point(30, 30))
    mouse.move_to(Point(20, 20))

    assert events == [MouseOutEvent(component, Point(20, 20))]
    assert parent_events == [MouseOutEvent(window, Point(10, 10))]

    mouse.move_to(Point(0, 0))

    assert events == [MouseOutEvent(component, Point(20, 20))]
    assert parent_events == [MouseOutEvent(window, Point(10, 10)), MouseOutEvent(window, Point(0, 0))]


# noinspection DuplicatedCode
def test_drag_start(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_drag_start.subscribe(events.append)
    window.on_drag_start.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))
    mouse.press(MouseButton.LEFT)

    mouse.move_to(Point(30, 30))
    mouse.release(MouseButton.LEFT)

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))
    mouse.press(MouseButton.RIGHT)
    mouse.move_to(Point(30, 30))

    assert events == []
    assert parent_events == [DragStartEvent(window, Point(20, 20), MouseButton.RIGHT)]

    mouse.release(MouseButton.RIGHT)

    mouse.press(MouseButton.MIDDLE)
    mouse.move_to(Point(20, 20))
    mouse.release(MouseButton.MIDDLE)

    assert events == [DragStartEvent(component, Point(30, 30), MouseButton.MIDDLE)]
    assert parent_events[1:] == [DragStartEvent(window, Point(30, 30), MouseButton.MIDDLE)]


# noinspection DuplicatedCode
def test_drag(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_drag.subscribe(events.append)
    window.on_drag.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))
    mouse.press(MouseButton.LEFT)

    mouse.move_to(Point(30, 30))
    mouse.release(MouseButton.LEFT)

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))
    mouse.press(MouseButton.RIGHT)
    mouse.move_to(Point(25, 25))
    mouse.move_to(Point(30, 30))

    assert events == []
    assert parent_events == [
        DragEvent(window, Point(25, 25), MouseButton.RIGHT),
        DragEvent(window, Point(30, 30), MouseButton.RIGHT)]

    mouse.release(MouseButton.RIGHT)

    mouse.press(MouseButton.MIDDLE)
    mouse.move_to(Point(20, 20))
    mouse.move_to(Point(10, 10))
    mouse.release(MouseButton.MIDDLE)

    assert events == [
        DragEvent(component, Point(20, 20), MouseButton.MIDDLE),
        DragEvent(component, Point(10, 10), MouseButton.MIDDLE)
    ]

    assert parent_events[2:] == [
        DragEvent(window, Point(20, 20), MouseButton.MIDDLE),
        DragEvent(window, Point(10, 10), MouseButton.MIDDLE)
    ]


def test_drag_over(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_drag_over.subscribe(events.append)
    window.on_drag_over.subscribe(parent_events.append)

    mouse.move_to(Point(10, 10))

    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(20, 20))
    mouse.move_to(Point(30, 30))
    mouse.release(MouseButton.LEFT)

    assert events == [DragOverEvent(component, Point(30, 30), MouseButton.LEFT)]
    assert parent_events == [DragOverEvent(window, Point(20, 20), MouseButton.LEFT)]

    mouse.move_to(Point(20, 20))
    mouse.press(MouseButton.RIGHT)
    mouse.move_to(Point(30, 30))
    mouse.move_to(Point(35, 35))

    assert events[1:] == [DragOverEvent(component, Point(30, 30), MouseButton.RIGHT)]
    assert parent_events[1:] == []

    mouse.release(MouseButton.RIGHT)

    mouse.press(MouseButton.MIDDLE)
    mouse.move_to(Point(20, 20))
    mouse.move_to(Point(10, 10))
    mouse.release(MouseButton.MIDDLE)

    assert events[2:] == []
    assert parent_events[1:] == []


def test_drag_leave(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_drag_leave.subscribe(events.append)
    window.on_drag_leave.subscribe(parent_events.append)

    mouse.move_to(Point(35, 35))
    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(30, 30))

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    assert events == [DragLeaveEvent(component, Point(20, 20), MouseButton.LEFT)]
    assert parent_events == []

    mouse.release(MouseButton.LEFT)
    mouse.press(MouseButton.RIGHT)

    mouse.move_to(Point(30, 30))
    mouse.release(MouseButton.RIGHT)

    assert events[1:] == []
    assert parent_events == []

    mouse.press(MouseButton.MIDDLE)
    mouse.move_to(Point(10, 10))

    assert events[1:] == [DragLeaveEvent(component, Point(10, 10), MouseButton.MIDDLE)]
    assert parent_events == [DragLeaveEvent(window, Point(10, 10), MouseButton.MIDDLE)]


def test_drag_end(mouse: FakeMouseInput, component: Component, window: Window):
    events = []
    parent_events = []

    component.on_drag_end.subscribe(events.append)
    window.on_drag_end.subscribe(parent_events.append)

    mouse.move_to(Point(30, 30))
    mouse.press(MouseButton.LEFT)

    assert events == []
    assert parent_events == []

    mouse.move_to(Point(20, 20))

    assert events == []
    assert parent_events == []

    mouse.release(MouseButton.LEFT)

    assert events == [DragEndEvent(component, Point(20, 20), MouseButton.LEFT)]
    assert parent_events == [DragEndEvent(window, Point(20, 20), MouseButton.LEFT)]

    mouse.press(MouseButton.RIGHT)

    mouse.move_to(Point(30, 30))
    mouse.release(MouseButton.RIGHT)

    assert events[1:] == []
    assert parent_events[1:] == [DragEndEvent(window, Point(30, 30), MouseButton.RIGHT)]
