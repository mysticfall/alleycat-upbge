from pytest import fixture

from cairocffi import ToyFontFace
from returns.maybe import Nothing, Some

from alleycat.ui import ColorChangeEvent, FontChangeEvent, Insets, InsetsChangeEvent, RGBA, StyleLookup


@fixture
def lookup() -> StyleLookup:
    return StyleLookup()


def test_lookup_color(lookup: StyleLookup):
    red = RGBA(1, 0, 0, 1)
    blue = RGBA(0, 0, 1, 1)

    red_key = "red"
    blue_key = "blue"

    lookup.set_color(red_key, red)
    lookup.set_color(blue_key, blue)

    assert lookup.get_color("green") == Nothing
    assert lookup.get_color(red_key).unwrap() == red
    assert lookup.get_color(blue_key).unwrap() == blue

    lookup.clear_color(blue_key)

    assert lookup.get_color(blue_key) == Nothing


def test_lookup_font(lookup: StyleLookup):
    sans = ToyFontFace("Sans")
    serif = ToyFontFace("Serif")

    label_key = "label"
    button_key = "button"

    lookup.set_font(label_key, sans)
    lookup.set_font(button_key, serif)

    assert lookup.get_font("dialog") == Nothing
    assert lookup.get_font(label_key).unwrap() == sans
    assert lookup.get_font(button_key).unwrap() == serif

    lookup.clear_font(label_key)

    assert lookup.get_font(label_key) == Nothing


def test_lookup_insets(lookup: StyleLookup):
    padding = Insets(5, 5, 5, 5)
    margin = Insets(10, 10, 10, 10)

    padding_key = "padding"
    margin_key = "margin"

    lookup.set_insets(padding_key, padding)
    lookup.set_insets(margin_key, margin)

    assert lookup.get_insets("button_padding") == Nothing
    assert lookup.get_insets(padding_key).unwrap() == padding
    assert lookup.get_insets(margin_key).unwrap() == margin

    lookup.clear_insets(padding_key)

    assert lookup.get_insets(padding_key) == Nothing


def test_on_style_change(lookup: StyleLookup):
    changes = []

    lookup.on_style_change.subscribe(changes.append)

    assert changes == []

    lookup.set_color("color1", RGBA(1, 0, 0, 1))
    lookup.set_color("color1", RGBA(1, 0, 0, 1))  # Should ignore duplicated requests.

    assert changes == [ColorChangeEvent(lookup, "color1", Some(RGBA(1, 0, 0, 1)))]

    lookup.set_color("color2", RGBA(0, 1, 0, 1))

    assert changes[1:] == [ColorChangeEvent(lookup, "color2", Some(RGBA(0, 1, 0, 1)))]

    lookup.set_color("color2", RGBA(0, 1, 1, 1))

    assert changes[2:] == [ColorChangeEvent(lookup, "color2", Some(RGBA(0, 1, 1, 1)))]

    font = ToyFontFace("Sans")

    lookup.set_font("font1", font)

    assert changes[3:] == [FontChangeEvent(lookup, "font1", Some(font))]

    lookup.clear_color("color1")
    lookup.clear_font("font1")

    assert changes[4:5] == [ColorChangeEvent(lookup, "color1", Nothing)]
    assert changes[5:6] == [FontChangeEvent(lookup, "font1", Nothing)]

    padding = Insets(5, 5, 5, 5)

    lookup.set_insets("padding", padding)

    assert changes[6:] == [InsetsChangeEvent(lookup, "padding", Some(padding))]

    lookup.clear_insets("padding")

    assert changes[7:] == [InsetsChangeEvent(lookup, "padding", Nothing)]
