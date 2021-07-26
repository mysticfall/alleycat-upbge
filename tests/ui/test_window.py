from typing import cast

from pytest import fixture, mark
from returns.maybe import Some

from alleycat.ui import Bounds, Context, Dimension, FakeMouseInput, Frame, MouseButton, MouseInput, Panel, Point, RGBA
from alleycat.ui.glass import StyleKeys
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def mouse(context: Context) -> FakeMouseInput:
    return cast(FakeMouseInput, MouseInput.input(context))


def test_style_fallback(context: Context):
    window = Frame(context)

    prefixes = list(window.style_fallback_prefixes)
    keys = list(window.style_fallback_keys(StyleKeys.Background))

    assert prefixes == ["Frame", "Window"]
    assert keys == ["Frame.background", "Window.background", "background"]


def test_draw(context: Context):
    window1 = Frame(context)

    window1.bounds = Bounds(10, 20, 80, 60)

    window2 = Frame(context)

    window2.bounds = Bounds(50, 40, 50, 50)
    window2.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    context.process()

    assert_image("draw", context)


def test_draw_children(context: Context):
    window = Frame(context)

    window.bounds = Bounds(10, 20, 80, 60)
    window.set_color(StyleKeys.Background, RGBA(0.5, 0.5, 0.5, 1))

    child1 = Panel(context)

    child1.bounds = Bounds(10, 10, 40, 40)
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    child2 = Panel(context)

    child2.bounds = Bounds(30, 30, 40, 40)
    child2.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    window.add(child1)
    window.add(child2)

    context.process()

    assert_image("draw_children", context)


def test_window_at(context: Context):
    manager = context.window_manager

    bottom = Frame(context)
    bottom.bounds = Bounds(0, 0, 100, 100)

    middle = Frame(context)
    middle.bounds = Bounds(100, 100, 100, 100)

    top = Frame(context)
    top.bounds = Bounds(50, 50, 100, 100)

    assert manager.window_at(Point(0, 0)) == Some(bottom)
    assert manager.window_at(Point(100, 0)) == Some(bottom)
    assert manager.window_at(Point(0, 100)) == Some(bottom)

    assert manager.window_at(Point(200, 100)) == Some(middle)
    assert manager.window_at(Point(200, 200)) == Some(middle)
    assert manager.window_at(Point(100, 200)) == Some(middle)

    assert manager.window_at(Point(100, 100)) == Some(top)
    assert manager.window_at(Point(150, 150)) == Some(top)
    assert manager.window_at(Point(150, 50)) == Some(top)
    assert manager.window_at(Point(50, 150)) == Some(top)


def test_drag(context: Context, mouse: FakeMouseInput):
    window = Frame(context)
    window.draggable = True
    window.resizable = True
    window.bounds = Bounds(10, 10, 50, 50)

    mouse.move_to(Point(30, 30))
    mouse.press(MouseButton.RIGHT)

    mouse.move_to(Point(40, 40))
    mouse.release(MouseButton.RIGHT)

    context.process()

    assert_image("drag_with_right_button", context)

    window.bounds = Bounds(10, 10, 50, 50)

    mouse.move_to(Point(20, 20))
    mouse.press(MouseButton.LEFT)

    mouse.move_to(Point(30, 40))
    mouse.release(MouseButton.LEFT)

    context.process()

    assert_image("drag_with_left_button", context)

    window.bounds = Bounds(10, 10, 50, 50)

    mouse.move_to(Point(10, 10))

    mouse.press(MouseButton.LEFT)
    mouse.press(MouseButton.MIDDLE)

    mouse.move_to(Point(40, 30))

    mouse.release(MouseButton.MIDDLE)

    mouse.move_to(Point(20, 50))

    context.process()

    assert_image("drag_with_2_buttons", context)

    mouse.release(MouseButton.LEFT)

    window.bounds = Bounds(10, 10, 50, 50)
    window.draggable = False

    mouse.move_to(Point(30, 30))
    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(50, 30))
    mouse.release(MouseButton.LEFT)

    context.process()

    assert_image("drag_non_draggable", context)


def test_drag_overlapping(context: Context, mouse: FakeMouseInput):
    bottom = Frame(context)
    bottom.draggable = True
    bottom.bounds = Bounds(10, 10, 50, 50)
    bottom.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    top = Frame(context)
    top.draggable = True
    top.bounds = Bounds(20, 20, 50, 50)
    top.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    mouse.move_to(Point(30, 30))
    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(50, 50))
    mouse.release(MouseButton.LEFT)

    context.process()

    assert_image("drag_overlapping_top", context)

    mouse.move_to(Point(20, 20))
    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(40, 40))
    mouse.release(MouseButton.LEFT)

    context.process()

    assert_image("drag_overlapping_bottom", context)


@mark.parametrize("name, drag_from, drag_to", (
        ("resize_North", Point(40, 25), Point(40, 10)),
        ("resize_Northeast", Point(75, 25), Point(90, 10)),
        ("resize_East", Point(75, 40), Point(90, 40)),
        ("resize_Southeast", Point(75, 75), Point(90, 90)),
        ("resize_South", Point(40, 75), Point(40, 90)),
        ("resize_Southwest", Point(25, 75), Point(10, 90)),
        ("resize_West", Point(25, 40), Point(10, 40)),
        ("resize_Northwest", Point(25, 25), Point(10, 10)),
        ("resize_North_shrink", Point(40, 25), Point(40, 40)),
        ("resize_Northeast_shrink", Point(75, 25), Point(60, 40)),
        ("resize_East_shrink", Point(75, 40), Point(60, 40)),
        ("resize_Southeast_shrink", Point(75, 75), Point(60, 60)),
        ("resize_South_shrink", Point(40, 75), Point(40, 50)),
        ("resize_Southwest_shrink", Point(25, 75), Point(40, 60)),
        ("resize_West_shrink", Point(25, 40), Point(40, 40)),
        ("resize_Northwest_shrink", Point(25, 25), Point(40, 40))
))
@mark.parametrize("resizable", (True, False))
def test_resize(
        name: str,
        drag_from: Point,
        drag_to: Point,
        resizable: bool,
        context: Context,
        mouse: FakeMouseInput):
    window = Frame(context)
    window.draggable = resizable
    window.resizable = resizable

    window.bounds = Bounds(20, 20, 60, 60)

    mouse.move_to(drag_from)
    mouse.press(MouseButton.LEFT)
    mouse.move_to(drag_to)
    mouse.release(MouseButton.LEFT)

    context.process()

    image = name if resizable else "resize_non_resizable"

    assert_image(image, context)


@mark.parametrize("drag_from, drag_to, expected", (
        (Point(40, 25), Point(40, 95), Bounds(20, 80, 60, 0)),
        (Point(75, 25), Point(5, 95), Bounds(20, 80, 0, 0)),
        (Point(75, 40), Point(5, 40), Bounds(20, 20, 0, 60)),
        (Point(75, 75), Point(5, 5), Bounds(20, 20, 0, 0)),
        (Point(40, 75), Point(40, 5), Bounds(20, 20, 60, 0)),
        (Point(25, 75), Point(95, 5), Bounds(80, 20, 0, 0)),
        (Point(25, 40), Point(95, 40), Bounds(80, 20, 0, 60)),
        (Point(25, 25), Point(95, 95), Bounds(80, 80, 0, 0))
))
def test_resize_to_collapse(
        drag_from: Point,
        drag_to: Point,
        expected: Bounds,
        context: Context,
        mouse: FakeMouseInput):
    window = Frame(context)
    window.draggable = True
    window.resizable = True

    window.bounds = Bounds(20, 20, 60, 60)

    mouse.move_to(drag_from)
    mouse.press(MouseButton.LEFT)
    mouse.move_to(drag_to)
    mouse.release(MouseButton.LEFT)

    context.process()

    assert window.bounds == expected


@mark.parametrize("drag_from, drag_to, expected", (
        (Point(40, 25), Point(40, 95), Bounds(20, 50, 60, 30)),
        (Point(75, 25), Point(5, 95), Bounds(20, 50, 30, 30)),
        (Point(75, 40), Point(5, 40), Bounds(20, 20, 30, 60)),
        (Point(75, 75), Point(5, 5), Bounds(20, 20, 30, 30)),
        (Point(40, 75), Point(40, 5), Bounds(20, 20, 60, 30)),
        (Point(25, 75), Point(95, 5), Bounds(50, 20, 30, 30)),
        (Point(25, 40), Point(95, 40), Bounds(50, 20, 30, 60)),
        (Point(25, 25), Point(95, 95), Bounds(50, 50, 30, 30))
))
def test_resize_with_min_size(
        drag_from: Point,
        drag_to: Point,
        expected: Bounds,
        context: Context,
        mouse: FakeMouseInput):
    window = Frame(context)
    window.draggable = True
    window.resizable = True

    window.minimum_size_override = Some(Dimension(30, 30))

    window.bounds = Bounds(20, 20, 60, 60)

    mouse.move_to(drag_from)
    mouse.press(MouseButton.LEFT)
    mouse.move_to(drag_to)
    mouse.release(MouseButton.LEFT)

    context.process()

    assert window.bounds == expected


def test_dispose(context: Context):
    manager = context.window_manager

    assert len(manager.windows) == 0

    window = Frame(context)

    assert len(manager.windows) == 1

    window.dispose()

    assert len(manager.windows) == 0
