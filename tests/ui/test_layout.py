from pytest import fixture
from returns.maybe import Some

from alleycat.ui import Bounds, Context, Dimension, Frame, Panel, RGBA
from alleycat.ui.glass import StyleKeys
from alleycat.ui.layout import Border, BorderLayout, VBoxLayout
from tests.ui import UI, assert_image


@fixture
def context() -> Context:
    return UI().create_context()


def test_nested_layout(context: Context):
    box = Frame(context, VBoxLayout())
    box.bounds = Bounds(0, 0, 100, 100)

    child1 = Panel(context)
    child1.preferred_size_override = Some(Dimension(50, 20))
    child1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    box.add(child1)

    child2 = Panel(context, BorderLayout())

    top = Panel(context)
    top.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))
    top.preferred_size_override = Some(Dimension(0, 20))

    child2.add(top, Border.Top)

    right = Panel(context)
    right.set_color(StyleKeys.Background, RGBA(0, 1, 0, 1))
    right.preferred_size_override = Some(Dimension(15, 0))

    child2.add(right, Border.Right)

    bottom = Panel(context)
    bottom.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))
    bottom.preferred_size_override = Some(Dimension(0, 15))

    child2.add(bottom, Border.Bottom)

    left = Panel(context)
    left.set_color(StyleKeys.Background, RGBA(1, 1, 1, 1))
    left.preferred_size_override = Some(Dimension(5, 0))

    child2.add(left, Border.Left)

    center = Panel(context)
    center.set_color(StyleKeys.Background, RGBA(0, 0, 0, 1))
    center.preferred_size_override = Some(Dimension(60, 20))

    child2.add(center, Border.Center)

    box.add(child2)

    child3 = Panel(context)
    child3.preferred_size_override = Some(Dimension(40, 20))
    child3.minimum_size_override = Some(Dimension(20, 10))
    child3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    box.add(child3)

    assert box.layout_pending
    context.process()
    assert not box.layout_pending

    assert_image("nested_layout", context)

    left.minimum_size_override = Some(Dimension(40, 0))
    top.preferred_size_override = Some(Dimension(0, 10))

    assert box.layout_pending
    context.process()
    assert not box.layout_pending

    assert_image("nested_layout_resize_nested_child", context)

    bottom.visible = False

    assert box.layout_pending
    context.process()
    assert not box.layout_pending

    assert_image("nested_layout_hide_nested_child", context)
