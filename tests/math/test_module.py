from pytest import mark

from alleycat.math import normalize_euler


@mark.parametrize("angle, expected", [
    (0, 0), (90, 90), (180, 180), (270, -90), (-0, 0), (-90, -90), (-180, 180), (-270, 90), (450, 90), (-450, -90)])
def test_normalize_euler(angle, expected):
    assert normalize_euler(angle) == expected
