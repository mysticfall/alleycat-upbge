from math import radians

from pytest import approx, mark

from alleycat.math import normalize_angle, normalize_euler

fixture = [
    (0, 0), (90, 90), (180, 180), (270, -90), (-0, 0), (-90, -90), (-180, 180), (-270, 90), (450, 90), (-450, -90)]


@mark.parametrize("angle, expected", fixture)
def test_normalize_angle(angle, expected):
    assert normalize_angle(radians(angle)) == approx(radians(expected))


@mark.parametrize("angle, expected", fixture)
def test_normalize_euler(angle, expected):
    assert normalize_euler(angle) == expected
