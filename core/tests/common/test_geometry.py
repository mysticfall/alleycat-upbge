from alleycat.common import Point2D


def test_point2d_init():
    point = Point2D(10.5, -20.2)

    assert point.x == 10.5
    assert point.y == -20.2


def test_point2d_unpack():
    (x, y) = Point2D(20.2, 15.3)

    assert x == 20.2
    assert y == 15.3


def test_point2d_operations():
    assert Point2D(-10, 6) + Point2D(5, 2) == Point2D(-5, 8)
    assert Point2D(6.3, 0) - Point2D(2.3, 2.5) == Point2D(4., -2.5)
    assert Point2D(3, 5) * -2 == Point2D(-6, -10)
    assert Point2D(10.4, -3) / 2 == Point2D(5.2, -1.5)

    assert -Point2D(3, -6) == Point2D(-3, 6)


def test_point2d_to_tuple():
    assert Point2D(3, 2).tuple == (3, 2)


def test_point2d_from_tuple():
    assert Point2D.from_tuple((3, 2)) == Point2D(3, 2)


def test_point2d_iter():
    components = [p for p in Point2D(20, 5)]
    assert components == [20, 5]


def test_point2d_copy():
    assert Point2D(3, 2) == Point2D(1, 5).copy(x=3, y=2)
    assert Point2D(3, 5) == Point2D(1, 5).copy(x=3)
    assert Point2D(1, 2) == Point2D(1, 5).copy(y=2)
    assert Point2D(1, 5) == Point2D(1, 5).copy()
