from pytest import fixture

from alleycat.ui import Bounds, Context, Label, Panel, RGBA, Window
from alleycat.ui.glass import StyleKeys
from tests.ui import UI, assert_image


# noinspection DuplicatedCode
@fixture
def context() -> Context:
    return UI().create_context()


def test_style_fallback(context: Context):
    label = Label(context)

    prefixes = list(label.style_fallback_prefixes)
    keys = list(label.style_fallback_keys(StyleKeys.Background))

    assert prefixes == ["Label"]
    assert keys == ["Label.background", "background"]


def test_draw(context: Context):
    context.look_and_feel.set_color("Panel.background", RGBA(0, 0, 1, 0.5))

    window = Window(context)
    window.bounds = Bounds(0, 0, 100, 100)

    panel1 = Panel(context)
    panel1.bounds = Bounds(20, 20, 40, 60)

    panel2 = Panel(context)
    panel2.bounds = Bounds(50, 40, 40, 40)
    panel2.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    window.add(panel1)
    window.add(panel2)

    context.process()

    assert_image("draw", context)
