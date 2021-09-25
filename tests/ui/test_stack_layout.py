from pytest import fixture, mark
from returns.maybe import Some

from alleycat.ui import Bounds, Container, Context, Dimension, Frame, Insets, Layout, Panel, RGBA
from alleycat.ui.glass import StyleKeys
from alleycat.ui.layout import StackLayout
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def layout() -> StackLayout:
    return StackLayout()


@fixture
def container(layout: Layout, context: Context) -> Container:
    frame = Frame(context, layout)
    frame.bounds = Bounds(0, 0, 100, 100)

    return frame


# noinspection DuplicatedCode
def test_layout(container: Container, context: Context):
    child1 = Panel(context)
    child1.bounds = Bounds(10, 10, 20, 20)
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    child2 = Panel(context)
    child2.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))
    child2.preferred_size_override = Some(Dimension(80, 60))

    child3 = Panel(context)
    child3.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))
    child3.preferred_size_override = Some(Dimension(60, 40))

    container.add(child1)
    container.add(child2, fill=False)
    container.add(child3, False)

    context.process()

    assert_image("stack", context)

    child4 = Panel(context)
    child4.set_color(StyleKeys.Background, RGBA(0, 1, 1, 1))

    container.add(child4, fill=True)

    context.process()

    assert_image("stack-fill", context)

    container.add(child3, True)

    context.process()

    assert_image("stack-fill2", context)


# noinspection DuplicatedCode
@mark.parametrize("padding", (Insets(10, 10, 10, 10), Insets(15, 0, 15, 0), Insets(0, 10, 20, 0)))
def test_layout_with_insets(padding: Insets, layout: StackLayout, container: Container, context: Context):
    child1 = Panel(context)
    child1.bounds = Bounds(10, 10, 20, 20)
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    child2 = Panel(context)
    child2.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))
    child2.preferred_size_override = Some(Dimension(80, 60))

    container.add(child1)
    container.add(child2, fill=False)

    layout.padding = padding

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    name = f"stack-{padding.top},{padding.right},{padding.bottom},{padding.left}"

    assert_image(name, context)
