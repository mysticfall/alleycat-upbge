from typing import Set

from pytest import fixture, mark
from returns.iterables import Fold
from returns.maybe import Nothing, Some

from alleycat.ui import Bounds, Component, Container, Context, Dimension, Frame, Insets, Panel, RGBA
from alleycat.ui.glass import StyleKeys
from alleycat.ui.layout import Border, BorderItem, BorderLayout
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def layout() -> BorderLayout:
    return BorderLayout()


@fixture
def container(layout: BorderLayout, context: Context) -> Container:
    container = Frame(context, layout)
    container.bounds = Bounds(5, 5, 90, 90)

    return container


def populate(areas: Set[Border], container: Container) -> Container:
    context = container.context

    if Border.Top in areas:
        top = Panel(context)
        top.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))
        top.preferred_size_override = Some(Dimension(0, 20))

        container.add(top, Border.Top)

    if Border.Right in areas:
        right = Panel(context)
        right.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))
        right.preferred_size_override = Some(Dimension(15, 0))

        container.add(right, Border.Right)

    if Border.Bottom in areas:
        bottom = Panel(context)
        bottom.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))
        bottom.preferred_size_override = Some(Dimension(0, 20))

        container.add(bottom, Border.Bottom)

    if Border.Left in areas:
        left = Panel(context)
        left.set_color(StyleKeys.Background, RGBA(1, 1, 1, 1))
        left.preferred_size_override = Some(Dimension(5, 0))

        container.add(left, Border.Left)

    if Border.Center in areas:
        center = Panel(context)
        center.set_color(StyleKeys.Background, RGBA(0, 0, 0, 1))

        container.add(center, Border.Center)

    return container


@mark.parametrize("border", Border)
def test_layout(border: Border, container: Container, context: Context):
    populate({border}, container)

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    assert_image(f"border-{border.name}", context)


@mark.parametrize("areas", (
        {Border.Center, Border.Top},
        {Border.Center, Border.Left, Border.Right},
        {Border.Center, Border.Top, Border.Right},
        {Border.Center, Border.Top, Border.Bottom},
        {Border.Left, Border.Right},
        {Border.Top, Border.Bottom},
        {Border.Center, Border.Top, Border.Left, Border.Right},
        {Border.Center, Border.Top, Border.Bottom, Border.Right},
        set(Border)
))
def test_layout_multiple_items(areas: Set[Border], container: Container, context: Context):
    populate(areas, container)

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    names = sorted(map(lambda a: a.name, areas))

    assert_image(f"border-{'-'.join(names)}", context)


@mark.parametrize("border", Border)
def test_item_visibility_multiple_items(border: Border, layout: BorderLayout, container: Container, context: Context):
    populate(set(Border), container)

    for b in Border:
        layout.areas[b].component.map(lambda c: setattr(c, "visible", b == Border))

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    assert_image(f"border-{border.name}", context)


@mark.parametrize("areas", (
        {Border.Center, Border.Top},
        {Border.Center, Border.Left, Border.Right},
        {Border.Center, Border.Top, Border.Right},
        {Border.Center, Border.Top, Border.Bottom},
        {Border.Left, Border.Right},
        {Border.Top, Border.Bottom},
        {Border.Center, Border.Top, Border.Left, Border.Right},
        {Border.Center, Border.Top, Border.Bottom, Border.Right},
        set(Border)
))
def test_item_visibility_multiple_items(areas: Set[Border], layout: BorderLayout, container: Container,
                                        context: Context):
    populate(set(Border), container)

    for b in Border:
        layout.areas[b].component.map(lambda c: setattr(c, "visible", b in areas))

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    names = sorted(map(lambda a: a.name, areas))

    assert_image(f"border-{'-'.join(names)}", context)


def test_items(layout: BorderLayout, container: Container, context: Context):
    child1 = Panel(context)
    child2 = Panel(context)
    child3 = Panel(context)
    child4 = Panel(context)
    child5 = Panel(context)

    container.add(child1)
    container.add(child2, Border.Left)
    container.add(child3, Border.Top, Insets(2, 2, 2, 2))
    container.add(child4, Border.Right, padding=Insets(5, 5, 5, 5))
    container.add(child5, region=Border.Bottom, padding=Insets(10, 10, 10, 10))

    def assert_item(item: BorderItem, child: Component, border: Border, padding: Insets) -> None:
        assert item.component.unwrap() == child
        assert item.border == border
        assert item.padding == padding

    assert_item(layout.areas[Border.Center], child1, Border.Center, Insets(0, 0, 0, 0))
    assert_item(layout.areas[Border.Top], child3, Border.Top, Insets(2, 2, 2, 2))
    assert_item(layout.areas[Border.Right], child4, Border.Right, Insets(5, 5, 5, 5))
    assert_item(layout.areas[Border.Bottom], child5, Border.Bottom, Insets(10, 10, 10, 10))
    assert_item(layout.areas[Border.Left], child2, Border.Left, Insets(0, 0, 0, 0))

    container.add(child1, Border.Right)
    container.remove(child2)
    container.remove(child3)

    assert_item(layout.areas[Border.Right], child1, Border.Right, Insets(0, 0, 0, 0))

    # noinspection PyTypeChecker
    children = Fold.collect_all(map(lambda a: a.component, layout.areas.values()), Some(())).unwrap()

    assert set(children) == {child5, child1}
    assert layout.areas[Border.Top].component == Nothing
    assert layout.areas[Border.Right].component == Some(child1)
    assert layout.areas[Border.Bottom].component == Some(child5)
    assert layout.areas[Border.Left].component == Nothing
