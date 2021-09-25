from typing import cast

from alleycat.reactive import functions as rv
from pytest import approx, fixture, mark
from returns.maybe import Nothing, Some

from alleycat.ui import Bounds, Context, Dimension, FakeMouseInput, Insets, LabelButton, LabelUI, MouseButton, \
    MouseInput, Point, RGBA, StyleLookup, TextAlign, Window
from alleycat.ui.glass import StyleKeys
from tests.ui import UI, assert_image

Tolerance: float = 8

TextTolerance: float = 2.5


@fixture
def context() -> Context:
    return UI().create_context()


@fixture
def mouse(context: Context) -> FakeMouseInput:
    return cast(FakeMouseInput, MouseInput.input(context))


def test_style_fallback(context: Context):
    button = LabelButton(context)

    prefixes = list(button.style_fallback_prefixes)
    keys = list(button.style_fallback_keys(StyleKeys.Background))

    assert prefixes == ["LabelButton", "Button"]
    assert keys == ["LabelButton.background", "Button.background", "background"]


def test_draw(context: Context):
    window = Window(context)
    window.bounds = Bounds(0, 0, 100, 100)

    button1 = LabelButton(context)

    button1.text = "Text"
    button1.bounds = Bounds(20, 10, 40, 20)

    button2 = LabelButton(context)

    button2.text = "AlleyCat"
    button2.text_size = 16
    button2.set_color(StyleKeys.Text, RGBA(1, 0, 0, 1))
    button2.bounds = Bounds(10, 50, 80, 30)

    window.add(button1)
    window.add(button2)

    context.process()

    assert_image("draw", context, tolerance=Tolerance)


# noinspection DuplicatedCode
@mark.parametrize("align", TextAlign)
@mark.parametrize("vertical_align", TextAlign)
def test_align(align: TextAlign, vertical_align: TextAlign, context: Context):
    window = Window(context)
    window.bounds = Bounds(0, 0, 100, 100)

    button = LabelButton(context)

    button.text = "AlleyCat"
    button.text_size = 16
    button.bounds = Bounds(0, 0, 100, 100)

    window.add(button)

    context.process()
    assert_image("align_default", context, tolerance=Tolerance)

    button.text_align = align
    button.text_vertical_align = vertical_align

    test_name = f"align_{align}_{vertical_align}".replace("TextAlign.", "")

    context.process()
    assert_image(test_name, context, tolerance=Tolerance)


# noinspection DuplicatedCode
def test_hover(context: Context, mouse: FakeMouseInput):
    window = Window(context)
    window.bounds = Bounds(0, 0, 100, 60)

    button = LabelButton(context)

    button.text = "AlleyCat"
    button.text_size = 14
    button.bounds = Bounds(10, 10, 80, 40)

    window.add(button)

    values = []

    rv.observe(button, "hover").subscribe(values.append)

    assert not button.hover
    assert values == [False]

    mouse.move_to(Point(50, 30))
    context.process()

    assert button.hover
    assert values == [False, True]
    assert_image("hover_mouse_over", context, tolerance=Tolerance)

    mouse.move_to(Point(0, 0))
    context.process()

    assert not button.hover
    assert values == [False, True, False]
    assert_image("hover_mouse_out", context, tolerance=Tolerance)

    mouse.move_to(Point(10, 10))
    context.process()

    assert button.hover
    assert values == [False, True, False, True]
    assert_image("hover_mouse_over2", context, tolerance=Tolerance)


# noinspection DuplicatedCode
def test_active(context: Context, mouse: FakeMouseInput):
    window = Window(context)
    window.bounds = Bounds(0, 0, 100, 60)

    button = LabelButton(context)

    button.text = "AlleyCat"
    button.text_size = 14
    button.bounds = Bounds(10, 10, 80, 40)

    window.add(button)

    values = []

    rv.observe(button, "active").subscribe(values.append)

    assert not button.active
    assert values == [False]

    mouse.move_to(Point(50, 30))
    mouse.press(MouseButton.LEFT)
    context.process()

    assert button.active
    assert values == [False, True]
    assert_image("active_mouse_down", context, tolerance=Tolerance)

    mouse.release(MouseButton.LEFT)
    context.process()

    assert not button.active
    assert values == [False, True, False]
    assert_image("active_mouse_up", context, tolerance=Tolerance)

    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(0, 0))
    context.process()

    assert button.active
    assert values == [False, True, False, True]
    assert_image("active_mouse_drag_out", context, tolerance=Tolerance)

    mouse.release(MouseButton.LEFT)
    mouse.press(MouseButton.LEFT)
    mouse.move_to(Point(50, 30))
    context.process()

    assert not button.active
    assert values == [False, True, False, True, False]
    assert_image("active_mouse_drag_in", context, tolerance=Tolerance)

    mouse.release(MouseButton.LEFT)
    mouse.press(MouseButton.RIGHT)
    context.process()

    assert not button.active
    assert values == [False, True, False, True, False]
    assert_image("active_right_button", context, tolerance=Tolerance)


# noinspection DuplicatedCode
def test_validation(context: Context):
    laf = context.look_and_feel
    fonts = context.toolkit.fonts

    button = LabelButton(context)
    button.validate()

    assert button.valid

    button.text = "Button"

    assert not button.valid

    button.validate()
    button.text_size = 20

    assert not button.valid

    button.validate()
    button.text_align = TextAlign.End
    button.text_vertical_align = TextAlign.End

    assert button.valid

    def test_style(lookup: StyleLookup):
        button.validate()

        lookup.set_font("NonExistentKey", fonts["Font1"])
        lookup.set_insets("NonExistentKey", Insets(10, 10, 10, 10))

        assert button.valid

        lookup.set_font(StyleKeys.Text, fonts["Font1"])

        assert not button.valid

        button.validate()
        lookup.set_insets(StyleKeys.Padding, Insets(10, 10, 10, 10))

        assert not button.valid

    test_style(laf)
    test_style(button)


# noinspection DuplicatedCode
def test_ui_extents(context: Context):
    button = LabelButton(context)
    ui = cast(LabelUI, button.ui)

    assert ui.extents(button) == Dimension(0, 0)

    button.text = "Test"
    button.validate()

    assert ui.extents(button).width == approx(20.02, abs=TextTolerance)
    assert ui.extents(button).height == approx(7.227, abs=TextTolerance)

    button.text_size = 15
    button.validate()

    assert ui.extents(button).width == approx(30.03, abs=TextTolerance)
    assert ui.extents(button).height == approx(10.840, abs=TextTolerance)


# noinspection DuplicatedCode
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(5, 5, 5, 5), Insets(10, 5, 0, 3)))
def test_minimum_size(padding: Insets, context: Context):
    with LabelButton(context) as button:
        calculated = []

        button.set_insets(StyleKeys.Padding, padding)
        button.validate()

        pw = padding.left + padding.right
        ph = padding.top + padding.bottom

        rv.observe(button.minimum_size).subscribe(calculated.append)

        assert button.minimum_size_override == Nothing
        assert button.minimum_size == Dimension(pw, ph)
        assert calculated == [Dimension(pw, ph)]

        button.text = "Test"
        button.validate()

        assert len(calculated) == 2

        assert button.minimum_size_override == Nothing

        assert button.minimum_size.width == approx(20.02 + pw, abs=TextTolerance)
        assert button.minimum_size.height == approx(7.227 + ph, abs=TextTolerance)

        assert calculated[1].width == approx(20.02 + pw, abs=TextTolerance)
        assert calculated[1].height == approx(7.227 + ph, abs=TextTolerance)

        assert button.bounds == Bounds(0, 0, calculated[1].width, calculated[1].height)

        button.text_size = 15
        button.validate()

        assert len(calculated) == 3

        assert button.minimum_size_override == Nothing

        assert button.minimum_size.width == approx(30.03 + pw, abs=TextTolerance)
        assert button.minimum_size.height == approx(10.840 + ph, abs=TextTolerance)

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        button.bounds = Bounds(10, 20, 60, 40)

        assert button.bounds == Bounds(10, 20, 60, 40)

        button.minimum_size_override = Some(Dimension(80, 50))
        button.validate()

        assert button.minimum_size_override == Some(Dimension(80, 50))
        assert button.minimum_size == Dimension(80, 50)

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        assert button.bounds == Bounds(10, 20, 80, 50)

        button.bounds = Bounds(0, 0, 30, 40)

        assert button.bounds == Bounds(0, 0, 80, 50)


# noinspection DuplicatedCode
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(5, 5, 5, 5), Insets(10, 5, 0, 3)))
def test_preferred_size(padding: Insets, context: Context):
    with LabelButton(context) as button:
        calculated = []

        button.set_insets(StyleKeys.Padding, padding)
        button.validate()

        pw = padding.left + padding.right
        ph = padding.top + padding.bottom

        rv.observe(button.preferred_size).subscribe(calculated.append)

        assert button.preferred_size_override == Nothing
        assert button.preferred_size == Dimension(pw, ph)
        assert calculated == [Dimension(pw, ph)]

        button.text = "Test"
        button.validate()

        assert len(calculated) == 2

        assert button.preferred_size_override == Nothing

        assert button.preferred_size.width == approx(20.02 + pw, abs=TextTolerance)
        assert button.preferred_size.height == approx(7.227 + ph, abs=TextTolerance)

        assert len(calculated) == 2

        assert calculated[1].width == approx(20.02 + pw, abs=TextTolerance)
        assert calculated[1].height == approx(7.227 + ph, abs=TextTolerance)

        button.text_size = 15
        button.validate()

        assert len(calculated) == 3

        assert button.preferred_size_override == Nothing

        assert button.preferred_size.width == approx(30.03 + pw, abs=TextTolerance)
        assert button.preferred_size.height == approx(10.840 + ph, abs=TextTolerance)

        assert len(calculated) == 3

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        button.preferred_size_override = Some(Dimension(80, 50))
        button.validate()

        assert button.preferred_size_override == Some(Dimension(80, 50))
        assert button.preferred_size == Dimension(80, 50)
        assert len(calculated) == 4
        assert calculated[3] == Dimension(80, 50)

        button.preferred_size_override = Some(Dimension(10, 10))
        button.validate()

        assert button.preferred_size == calculated[2]
        assert len(calculated) == 5
        assert calculated[4] == calculated[2]

        button.minimum_size_override = Some(Dimension(400, 360))
        button.validate()

        assert button.preferred_size == Dimension(400, 360)
        assert len(calculated) == 6
        assert calculated[5] == Dimension(400, 360)
