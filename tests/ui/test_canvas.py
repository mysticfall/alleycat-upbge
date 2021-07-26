from pathlib import Path

from pytest import fixture, mark
from returns.maybe import Some

from alleycat.ui import Bounds, Canvas, Context, Dimension, Frame, Image, Insets, RGBA, StyleLookup
from alleycat.ui.glass import StyleKeys
from tests.ui import UI, assert_image

Tolerance: float = 3


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def image(context: Context) -> Image:
    path = str(Path(__file__).parent.joinpath("fixtures/cat.png"))

    return context.toolkit.images[path]


def test_style_fallback(context: Context):
    canvas = Canvas(context)

    prefixes = list(canvas.style_fallback_prefixes)
    keys = list(canvas.style_fallback_keys(StyleKeys.Background))

    assert prefixes == ["Canvas"]
    assert keys == ["Canvas.background", "background"]


def test_validation(image: Image, context: Context):
    canvas = Canvas(context)
    canvas.validate()

    assert canvas.valid

    canvas.image = Some(image)

    assert not canvas.valid

    canvas.validate()

    assert canvas.valid

    def test_style(lookup: StyleLookup):
        canvas.validate()

        lookup.set_insets("NonExistentKey", Insets(10, 10, 10, 10))

        assert canvas.valid

        canvas.validate()
        lookup.set_insets(StyleKeys.Padding, Insets(10, 10, 10, 10))

        assert not canvas.valid

    test_style(context.look_and_feel)
    test_style(canvas)


def test_draw(image: Image, context: Context):
    window = Frame(context)
    window.bounds = Bounds(0, 0, 100, 100)

    canvas1 = Canvas(context)
    canvas1.bounds = Bounds(30, 40, 80, 30)
    canvas1.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    canvas2 = Canvas(context, image)
    canvas2.bounds = Bounds(0, 10, 64, 64)

    canvas3 = Canvas(context, image)
    canvas3.bounds = Bounds(10, 70, 80, 20)
    canvas3.set_color(StyleKeys.Background, RGBA(0, 0, 1, 1))

    window.add(canvas1)
    window.add(canvas2)
    window.add(canvas3)

    context.process()

    assert_image("draw", context, tolerance=Tolerance)


@mark.parametrize("size, padding", (
        (Dimension(100, 100), Insets(0, 0, 0, 0)),
        (Dimension(100, 100), Insets(10, 5, 3, 15)),
        (Dimension(64, 64), Insets(0, 0, 0, 0)),
        (Dimension(64, 64), Insets(10, 5, 3, 15))
))
def test_draw_with_padding(image: Image, size: Dimension, padding: Insets, context: Context):
    window = Frame(context)
    window.bounds = Bounds(0, 0, 100, 100)

    canvas = Canvas(context, image)
    canvas.set_color(StyleKeys.Background, RGBA(1, 0, 0, 1))

    window.add(canvas)

    (w, h) = size.tuple
    (top, right, bottom, left) = padding.tuple

    canvas.bounds = Bounds(0, 0, w, h)
    canvas.padding = padding

    context.process()

    assert_image(f"draw_with_padding-{top},{right},{bottom},{left}-{w}x{h}", context, tolerance=Tolerance)
