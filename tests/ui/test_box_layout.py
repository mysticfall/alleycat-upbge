from pytest import fixture, mark
from returns.maybe import Some

from alleycat.ui import Bounds, Context, Dimension, Frame, Insets, Panel, RGBA
from alleycat.ui.glass import StyleKeys
from alleycat.ui.layout import BoxAlign, BoxDirection, HBoxLayout, VBoxLayout
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


# noinspection DuplicatedCode
@mark.parametrize("direction", BoxDirection)
@mark.parametrize("spacing", (0, 10))
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(15, 20, 10, 5)))
@mark.parametrize("align", BoxAlign)
def test_hbox_layout(direction: BoxDirection, spacing: float, padding: Insets, align: BoxAlign, context: Context):
    layout = HBoxLayout()

    container = Frame(context, layout)
    container.bounds = Bounds(5, 5, 90, 90)

    child1 = Panel(context)
    child1.preferred_size_override = Some(Dimension(20, 50))
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    container.add(child1)

    child2 = Panel(context)
    child2.preferred_size_override = Some(Dimension(15, 60))
    child2.minimum_size_override = Some(Dimension(15, 60))
    child2.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))

    container.add(child2)

    child3 = Panel(context)
    child3.preferred_size_override = Some(Dimension(30, 40))
    child3.minimum_size_override = Some(Dimension(10, 20))
    child3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    container.add(child3)

    container.bounds = Bounds(5, 5, 90, 90)

    layout.spacing = spacing
    layout.padding = padding
    layout.align = align

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    (top, right, bottom, left) = padding.tuple

    prefix = f"hbox-{direction.name}-{spacing}-{top},{right},{bottom},{left}-{align.name}-"

    assert_image(prefix + "full-size", context)

    container.bounds = Bounds(5, 5, 45, 45)

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    assert_image(prefix + "half-size", context)


# noinspection DuplicatedCode
@mark.parametrize("child1_visible", (True, False))
@mark.parametrize("child2_visible", (True, False))
@mark.parametrize("child3_visible", (True, False))
def test_hbox_hide_child(child1_visible: bool, child2_visible: bool, child3_visible: bool, context: Context):
    container = Frame(context, HBoxLayout())
    container.bounds = Bounds(0, 0, 100, 100)

    child1 = Panel(context)
    child1.preferred_size_override = Some(Dimension(20, 50))
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    container.add(child1)

    child2 = Panel(context)
    child2.preferred_size_override = Some(Dimension(15, 60))
    child2.minimum_size_override = Some(Dimension(15, 60))
    child2.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))

    container.add(child2)

    child3 = Panel(context)
    child3.preferred_size_override = Some(Dimension(30, 40))
    child3.minimum_size_override = Some(Dimension(10, 20))
    child3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    container.add(child3)

    child1.visible = child1_visible
    child2.visible = child2_visible
    child3.visible = child3_visible

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    name = f"hbox-visibility-{child1_visible}-{child2_visible}-{child3_visible}"

    assert_image(name, context)


# noinspection DuplicatedCode
@mark.parametrize("direction", BoxDirection)
@mark.parametrize("spacing", (0, 10))
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(15, 20, 10, 5)))
@mark.parametrize("align", BoxAlign)
def test_vbox_layout(direction: BoxDirection, spacing: float, padding: Insets, align: BoxAlign, context: Context):
    layout = VBoxLayout()

    container = Frame(context, layout)
    container.bounds = Bounds(5, 5, 90, 90)

    child1 = Panel(context)
    child1.preferred_size_override = Some(Dimension(50, 20))
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    container.add(child1)

    child2 = Panel(context)
    child2.preferred_size_override = Some(Dimension(60, 15))
    child2.minimum_size_override = Some(Dimension(60, 15))
    child2.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))

    container.add(child2)

    child3 = Panel(context)
    child3.preferred_size_override = Some(Dimension(40, 30))
    child3.minimum_size_override = Some(Dimension(20, 10))
    child3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    container.add(child3)

    container.bounds = Bounds(5, 5, 90, 90)

    layout.spacing = spacing
    layout.padding = padding
    layout.align = align

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    (top, right, bottom, left) = padding.tuple

    prefix = f"vbox-{direction.name}-{spacing}-{top},{right},{bottom},{left}-{align.name}-"

    assert_image(prefix + "full-size", context)

    container.bounds = Bounds(5, 5, 45, 45)

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    assert_image(prefix + "half-size", context)


# noinspection DuplicatedCode
@mark.parametrize("child1_visible", (True, False))
@mark.parametrize("child2_visible", (True, False))
@mark.parametrize("child3_visible", (True, False))
def test_vbox_hide_child(child1_visible: bool, child2_visible: bool, child3_visible: bool, context: Context):
    container = Frame(context, VBoxLayout())
    container.bounds = Bounds(0, 0, 100, 100)

    child1 = Panel(context)
    child1.preferred_size_override = Some(Dimension(50, 20))
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    container.add(child1)

    child2 = Panel(context)
    child2.preferred_size_override = Some(Dimension(60, 15))
    child2.minimum_size_override = Some(Dimension(60, 15))
    child2.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))

    container.add(child2)

    child3 = Panel(context)
    child3.preferred_size_override = Some(Dimension(40, 30))
    child3.minimum_size_override = Some(Dimension(20, 10))
    child3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    container.add(child3)

    child1.visible = child1_visible
    child2.visible = child2_visible
    child3.visible = child3_visible

    assert container.layout_pending
    context.process()
    assert not container.layout_pending

    name = f"vbox-visibility-{child1_visible}-{child2_visible}-{child3_visible}"

    assert_image(name, context)
