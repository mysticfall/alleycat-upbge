from typing import Set, Tuple

from pytest import fixture, mark
from returns.maybe import Some

from alleycat.ui import Bounds, Component, Container, Context, Dimension, Frame, Panel, RGBA
from alleycat.ui.glass import StyleKeys
from alleycat.ui.layout import Anchor, AnchorLayout, Direction
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def container(context: Context) -> Container:
    frame = Frame(context, AnchorLayout())
    frame.bounds = Bounds(0, 0, 100, 100)

    return frame


@fixture
def child(context: Context) -> Component:
    panel = Panel(context)
    panel.preferred_size_override = Some(Dimension(40, 30))
    panel.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    return panel


def test_no_anchor(child: Component, container: Container, context: Context):
    context.process()
    assert_image("no-anchor", context)

    child.preferred_size_override = Some(Dimension(120, 130))

    context.process()
    assert_image("no-anchor-over-sized", context)

    child.minimum_size_override = Some(Dimension(60, 40))
    container.bounds = Bounds(0, 0, 50, 50)

    context.process()
    assert_image("no-anchor-min-size", context)


def test_constraints(child: Component, container: Container, context: Context):
    container.add(child, Anchor(Direction.Right, 15))

    context.process()
    assert_image("constraints", context)

    container.add(child, Direction.Right, 15)

    context.process()
    assert_image("constraints", context)

    container.add(child, direction=Direction.Right, distance=15)

    context.process()
    assert_image("constraints", context)


@mark.parametrize("direction", Direction)
@mark.parametrize("distance", (0, 10))
def test_edges(direction: Direction, distance: float, child: Component, container: Container):
    prefix = f"edge-{direction.name}-{distance}"

    assert_layout(prefix, container, child, {Anchor(direction, distance)})


@mark.parametrize("corners", (
        (Anchor(Direction.Top), Anchor(Direction.Right)),
        (Anchor(Direction.Right), Anchor(Direction.Bottom)),
        (Anchor(Direction.Left), Anchor(Direction.Bottom)),
        (Anchor(Direction.Left), Anchor(Direction.Top))))
@mark.parametrize("direction", Direction)
@mark.parametrize("distance", (0, 10))
def test_corners(
        corners: Tuple[Anchor, Anchor],
        direction: Direction,
        distance: float,
        child: Component,
        container: Container):
    (c1, c2) = corners

    prefix = f"corner-{c1.direction.name}-{c2.direction.name}-{distance}"

    assert_layout(prefix, container, child, {Anchor(c1.direction, distance), Anchor(c2.direction, distance)})


@mark.parametrize("horizontal", (True, False))
@mark.parametrize("vertical", (True, False))
@mark.parametrize("distance", (0, 10))
def test_stretch(horizontal: bool, vertical: bool, distance: float, child: Component, container: Container):
    anchors = ()

    if horizontal:
        name = "both" if vertical else "horizontal"
        anchors += (Anchor(Direction.Left, distance), Anchor(Direction.Right, distance))
    else:
        name = "vertical" if vertical else "none"

    if vertical:
        anchors += (Anchor(Direction.Top, distance), Anchor(Direction.Bottom, distance))

    prefix = f"stretch-{name}-{distance}"

    assert_layout(prefix, container, child, set(anchors))


@mark.parametrize("direction", Direction)
@mark.parametrize("distance", (0, 10))
def test_stretch_three_corners(direction: Direction, distance: float, child: Component, container: Container):
    anchors = [Anchor(d, distance) for d in Direction if d != direction]

    prefix = f"stretch-except-{direction.name}-{distance}"

    assert_layout(prefix, container, child, set(anchors))


def assert_layout(prefix: str, parent: Container, child: Component, anchors: Set[Anchor]):
    context = parent.context

    child.preferred_size_override = Some(Dimension(60, 40))

    parent.add(child, *anchors)
    parent.bounds = Bounds(0, 0, 100, 100)

    context.process()
    assert_image(prefix, context)

    parent.bounds = Bounds(0, 0, 60, 60)

    context.process()
    assert_image(f"{prefix}-half-size", context)

    child.preferred_size_override = Some(Dimension(80, 60))
    child.minimum_size_override = Some(Dimension(60, 30))

    context.process()
    assert_image(f"{prefix}-min-size", context)

    parent.bounds = Bounds(0, 0, 100, 100)

    context.process()
    assert_image(f"{prefix}-pref-size", context)
