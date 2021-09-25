from typing import cast

from alleycat.reactive import functions as rv
from pytest import approx, fixture, mark
from returns.maybe import Nothing, Some

from alleycat.ui import Bounds, Context, Dimension, Frame, Insets, Label, LabelUI, RGBA, StyleLookup, TextAlign
from alleycat.ui.glass import StyleKeys
from tests.ui import UI, assert_image

Tolerance: float = 8

TextTolerance: float = 2.5


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
    window = Frame(context)
    window.bounds = Bounds(0, 0, 100, 60)

    label = Label(context)

    label.text = "Text"
    label.bounds = Bounds(0, 30, 60, 30)

    label2 = Label(context)

    label2.text = "AlleyCat"
    label2.text_size = 18
    label2.set_color(StyleKeys.Text, RGBA(1, 0, 0, 1))
    label2.bounds = Bounds(20, 0, 80, 60)

    window.add(label)
    window.add(label2)

    context.process()

    assert_image("draw", context, tolerance=Tolerance)


# noinspection DuplicatedCode
@mark.parametrize("align", TextAlign)
@mark.parametrize("vertical_align", TextAlign)
def test_align(align: TextAlign, vertical_align: TextAlign, context: Context):
    window = Frame(context)
    window.bounds = Bounds(0, 0, 100, 100)

    label = Label(context)

    label.text = "AlleyCat"
    label.text_size = 18
    label.bounds = Bounds(0, 0, 100, 100)

    window.add(label)

    context.process()
    assert_image("align_default", context, tolerance=Tolerance)

    label.text_align = align
    label.text_vertical_align = vertical_align

    test_name = f"align_{align}_{vertical_align}".replace("TextAlign.", "")

    context.process()
    assert_image(test_name, context, tolerance=Tolerance)


# noinspection DuplicatedCode
def test_validation(context: Context):
    laf = context.look_and_feel
    fonts = context.toolkit.fonts

    label = Label(context)
    label.validate()

    assert label.valid

    label.text = "Label"

    assert not label.valid

    label.validate()
    label.text_size = 20

    assert not label.valid

    label.validate()
    label.text_align = TextAlign.End
    label.text_vertical_align = TextAlign.End

    assert label.valid

    def test_style(lookup: StyleLookup):
        label.validate()

        lookup.set_font("NonExistentKey", fonts["Font1"])
        lookup.set_insets("NonExistentKey", Insets(10, 10, 10, 10))

        assert label.valid

        lookup.set_font(StyleKeys.Text, fonts["Font1"])

        assert not label.valid

        label.validate()
        lookup.set_insets(StyleKeys.Padding, Insets(10, 10, 10, 10))

        assert not label.valid

    test_style(laf)
    test_style(label)


# noinspection DuplicatedCode
def test_ui_extents(context: Context):
    label = Label(context)
    ui = cast(LabelUI, label.ui)

    assert ui.extents(label) == Dimension(0, 0)

    label.text = "Test"
    label.validate()

    assert ui.extents(label).width == approx(20.02, abs=TextTolerance)
    assert ui.extents(label).height == approx(7.227, abs=TextTolerance)

    label.text_size = 15
    label.validate()

    assert ui.extents(label).width == approx(30.03, abs=TextTolerance)
    assert ui.extents(label).height == approx(10.840, abs=TextTolerance)


# noinspection DuplicatedCode
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(5, 5, 5, 5), Insets(10, 5, 0, 3)))
def test_minimum_size(padding: Insets, context: Context):
    with Label(context) as label:
        calculated = []

        label.set_insets(StyleKeys.Padding, padding)
        label.validate()

        pw = padding.left + padding.right
        ph = padding.top + padding.bottom

        rv.observe(label.minimum_size).subscribe(calculated.append)

        assert label.minimum_size_override == Nothing
        assert label.minimum_size == Dimension(pw, ph)
        assert calculated == [Dimension(pw, ph)]

        label.text = "Test"
        label.validate()

        assert len(calculated) == 2

        assert label.minimum_size_override == Nothing

        assert label.minimum_size.width == approx(20.02 + pw, abs=TextTolerance)
        assert label.minimum_size.height == approx(7.227 + ph, abs=TextTolerance)
        assert calculated[1].width == approx(20.02 + pw, abs=TextTolerance)
        assert calculated[1].height == approx(7.227 + ph, abs=TextTolerance)

        assert label.bounds == Bounds(0, 0, calculated[1].width, calculated[1].height)

        label.text_size = 15
        label.validate()

        assert len(calculated) == 3

        assert label.minimum_size_override == Nothing

        assert label.minimum_size.width == approx(30.03 + pw, abs=TextTolerance)
        assert label.minimum_size.height == approx(10.840 + ph, abs=TextTolerance)

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        label.bounds = Bounds(10, 20, 60, 40)

        assert label.bounds == Bounds(10, 20, 60, 40)

        label.minimum_size_override = Some(Dimension(80, 50))
        label.validate()

        assert label.minimum_size_override == Some(Dimension(80, 50))
        assert label.minimum_size == Dimension(80, 50)

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        assert label.bounds == Bounds(10, 20, 80, 50)

        label.bounds = Bounds(0, 0, 30, 40)

        assert label.bounds == Bounds(0, 0, 80, 50)


# noinspection DuplicatedCode
@mark.parametrize("padding", (Insets(0, 0, 0, 0), Insets(5, 5, 5, 5), Insets(10, 5, 0, 3)))
def test_preferred_size(padding: Insets, context: Context):
    with Label(context) as label:
        calculated = []

        label.set_insets(StyleKeys.Padding, padding)
        label.validate()

        pw = padding.left + padding.right
        ph = padding.top + padding.bottom

        rv.observe(label.preferred_size).subscribe(calculated.append)

        assert label.preferred_size_override == Nothing
        assert label.preferred_size == Dimension(pw, ph)
        assert calculated == [Dimension(pw, ph)]

        label.text = "Test"
        label.validate()

        assert len(calculated) == 2

        assert label.preferred_size_override == Nothing
        assert label.preferred_size.width == approx(20.02 + pw, abs=TextTolerance)
        assert label.preferred_size.height == approx(7.227 + ph, abs=TextTolerance)

        assert len(calculated) == 2

        assert calculated[1].width == approx(20.02 + pw, abs=TextTolerance)
        assert calculated[1].height == approx(7.227 + ph, abs=TextTolerance)

        label.text_size = 15
        label.validate()

        assert len(calculated) == 3

        assert label.preferred_size_override == Nothing

        assert label.preferred_size.width == approx(30.03 + pw, abs=TextTolerance)
        assert label.preferred_size.height == approx(10.840 + ph, abs=TextTolerance)

        assert len(calculated) == 3

        assert calculated[2].width == approx(30.03 + pw, abs=TextTolerance)
        assert calculated[2].height == approx(10.840 + ph, abs=TextTolerance)

        label.preferred_size_override = Some(Dimension(80, 50))
        label.validate()

        assert label.preferred_size_override == Some(Dimension(80, 50))
        assert label.preferred_size == Dimension(80, 50)

        assert len(calculated) == 4
        assert calculated[3] == Dimension(80, 50)

        label.preferred_size_override = Some(Dimension(10, 10))
        label.validate()

        assert label.preferred_size == calculated[2]
        assert len(calculated) == 5
        assert calculated[4] == calculated[2]

        label.minimum_size_override = Some(Dimension(400, 360))
        label.validate()

        assert label.preferred_size == Dimension(400, 360)
        assert len(calculated) == 6
        assert calculated[5] == Dimension(400, 360)
