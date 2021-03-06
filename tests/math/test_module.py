from math import radians

from pytest import approx, mark, raises

from alleycat.math import clamp, normalize_angle, normalize_euler

fixture = [
    (0, 0), (90, 90), (180, 180), (270, -90), (-0, 0), (-90, -90), (-180, 180), (-270, 90), (450, 90), (-450, -90)]


@mark.parametrize("angle, expected", fixture)
def test_normalize_angle(angle, expected):
    assert normalize_angle(radians(angle)) == approx(radians(expected))


@mark.parametrize("angle, expected", fixture)
def test_normalize_euler(angle, expected):
    assert normalize_euler(angle) == expected


@mark.parametrize("value, min_value, max_value, expected",
                  [(1.2, 1.0, 2.0, 1.2), (-2.5, 1.0, 2.0, 1.0), (5.2, 1.0, 2.5, 2.5)])
def test_clamp(value, min_value, max_value, expected):
    assert clamp(value, min_value, max_value) == expected


def test_clamp_invalid_range():
    with raises(ValueError) as e:
        clamp(1, 3, 1)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "value (1) less than minimum (3)"
