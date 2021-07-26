from pytest import raises
from returns.maybe import Nothing

from alleycat.ui import Bounds, Dimension, Insets, Point, RGBA


def test_point_init():
    point = Point(10.5, -20.2)

    assert point.x == 10.5
    assert point.y == -20.2


def test_point_unpack():
    (x, y) = Point(20.2, 15.3)

    assert x == 20.2
    assert y == 15.3


def test_point_operations():
    assert Point(-10, 6) + Point(5, 2) == Point(-5, 8)
    assert Point(6.3, 0) - Point(2.3, 2.5) == Point(4., -2.5)
    assert Point(3, 5) * -2 == Point(-6, -10)
    assert Point(10.4, -3) / 2 == Point(5.2, -1.5)

    assert -Point(3, -6) == Point(-3, 6)


def test_point_to_tuple():
    assert Point(3, 2).tuple == (3, 2)


def test_point_from_tuple():
    assert Point.from_tuple((3, 2)) == Point(3, 2)


def test_point_copy():
    assert Point(3, 2) == Point(1, 5).copy(x=3, y=2)
    assert Point(3, 5) == Point(1, 5).copy(x=3)
    assert Point(1, 2) == Point(1, 5).copy(y=2)
    assert Point(1, 5) == Point(1, 5).copy()


def test_dimension_init():
    assert 120 == Dimension(120, 0).width
    assert 30.5 == Dimension(0, 30.5).height

    with raises(ValueError) as e_width:
        Dimension(-10, 30)

    assert e_width.value.args[0] == "Argument 'width' must be zero or a positive number."

    with raises(ValueError) as e_height:
        Dimension(30, -10)

    assert e_height.value.args[0] == "Argument 'height' must be zero or a positive number."


def test_dimension_unpack():
    (width, height) = Dimension(20, 10)

    assert width == 20
    assert height == 10


def test_dimension_to_tuple():
    assert Dimension(30, 20).tuple == (30, 20)


def test_dimension_from_tuple():
    assert Dimension.from_tuple((30, 0)) == Dimension(30, 0)


def test_dimension_copy():
    assert Dimension(10, 50).copy(width=30, height=20) == Dimension(30, 20)
    assert Dimension(10, 50).copy(width=30) == Dimension(30, 50)
    assert Dimension(10, 50).copy(height=20) == Dimension(10, 20)
    assert Dimension(10, 50).copy() == Dimension(10, 50)


def test_dimension_operations():
    assert Dimension(10, 6) + Dimension(5, 2) == Dimension(15, 8)
    assert Dimension(6.3, 5) - Dimension(2.3, 2.5) == Dimension(4, 2.5)
    assert Dimension(2.3, 5) - Dimension(6.3, 2.5) == Dimension(0, 2.5)
    assert Dimension(6.3, 2.5) - Dimension(2.3, 5) == Dimension(4, 0)
    assert Dimension(3, 5) * 2 == Dimension(6, 10)
    assert Dimension(10.4, 3) / 2 == Dimension(5.2, 1.5)


def test_bounds_init():
    assert Bounds(-5, 10, 120, 0).x == -5
    assert Bounds(15, -30, 0, 30.5).y == -30
    assert Bounds(-5, 10, 120, 0).width == 120
    assert Bounds(15, -30, 0, 30.5).height == 30.5

    with raises(ValueError) as e_width:
        Bounds(10, 0, -10, 30)

    assert e_width.value.args[0] == "Argument 'width' must be zero or a positive number."

    with raises(ValueError) as e_height:
        Bounds(-20, 30, 30, -10)

    assert e_height.value.args[0] == "Argument 'height' must be zero or a positive number."


def test_bounds_unpack():
    (x, y, width, height) = Bounds(10, -30, 150, 200)

    assert x == 10
    assert y == -30
    assert width == 150
    assert height == 200


def test_bounds_to_tuple():
    assert Bounds(30, 20, 100, 200).tuple == (30, 20, 100, 200)


def test_bounds_from_tuple():
    assert Bounds.from_tuple((30, 0, 50, 40)) == Bounds(30, 0, 50, 40)


def test_bounds_move_to():
    assert Bounds(20, 30, 100, 200).move_to(Point(-10, 20)) == Bounds(-10, 20, 100, 200)


def test_bounds_move_by():
    assert Bounds(20, 30, 100, 200).move_by(Point(-10, 20)) == Bounds(10, 50, 100, 200)


def test_bounds_copy():
    assert Bounds(-20, 10, 80, 30).copy(y=20, width=30) == Bounds(-20, 20, 30, 30)
    assert Bounds(-20, 10, 80, 30).copy(x=10, height=100) == Bounds(10, 10, 80, 100)
    assert Bounds(-20, 10, 80, 30).copy(x=0, y=0, width=20, height=40) == Bounds(0, 0, 20, 40)
    assert Bounds(-20, 10, 80, 30).copy() == Bounds(-20, 10, 80, 30)


def test_bounds_operations():
    assert Bounds(0, 0, 100, 200) + Point(20, 30) == Bounds(0, 0, 100, 200)
    assert Bounds(0, 0, 100, 200) + Point(80, 230) == Bounds(0, 0, 100, 230)
    assert Bounds(0, 0, 100, 200) + Point(120, 230) == Bounds(0, 0, 120, 230)
    assert Bounds(0, 0, 100, 200) + Point(-20, 30) == Bounds(-20, 0, 120, 200)
    assert Bounds(0, 0, 100, 200) + Point(-20, -30) == Bounds(-20, -30, 120, 230)

    assert Bounds(0, 0, 30, 30) + Bounds(20, 10, 30, 30) == Bounds(0, 0, 50, 40)
    assert Bounds(0, 0, 30, 30) + Bounds(-10, -20, 50, 30) == Bounds(-10, -20, 50, 30)
    assert Bounds(0, 0, 30, 30) + Bounds(10, 10, 20, 10) == Bounds(0, 0, 30, 30)

    assert Bounds(20, 40, 100, 200) * 2 == Bounds(20, 40, 200, 400)
    assert Bounds(20, 40, 200, 400) / 2 == Bounds(20, 40, 100, 200)

    assert Bounds(10, 20, 100, 60) & Bounds(120, 20, 100, 60) == Nothing
    assert Bounds(10, 20, 100, 60) & Bounds(-120, 20, 100, 60) == Nothing
    assert Bounds(10, 20, 100, 60) & Bounds(10, 90, 100, 60) == Nothing
    assert Bounds(10, 20, 100, 60) & Bounds(10, -50, 100, 60) == Nothing

    assert (Bounds(10, 20, 100, 60) & Bounds(-60, -20, 100, 60)).unwrap() == Bounds(10, 20, 30, 20)
    assert (Bounds(10, 20, 100, 60) & Bounds(60, -20, 100, 60)).unwrap() == Bounds(60, 20, 50, 20)
    assert (Bounds(10, 20, 100, 60) & Bounds(60, 40, 100, 60)).unwrap() == Bounds(60, 40, 50, 40)
    assert (Bounds(10, 20, 100, 60) & Bounds(-60, 40, 100, 60)).unwrap() == Bounds(10, 40, 30, 40)

    assert (Bounds(10, 20, 100, 60) & Bounds(40, 30, 100, 40)).unwrap() == Bounds(40, 30, 70, 40)
    assert (Bounds(10, 20, 100, 60) & Bounds(-20, 30, 100, 40)).unwrap() == Bounds(10, 30, 70, 40)
    assert (Bounds(10, 20, 100, 60) & Bounds(20, -20, 80, 60)).unwrap() == Bounds(20, 20, 80, 20)
    assert (Bounds(10, 20, 100, 60) & Bounds(20, 40, 80, 60)).unwrap() == Bounds(20, 40, 80, 40)

    assert (Bounds(10, 20, 100, 60) & Bounds(30, 40, 50, 20)).unwrap() == Bounds(30, 40, 50, 20)

    assert Bounds(10, 20, 100, 60) + Insets(5, 10, 5, 20) == Bounds(-10, 15, 130, 70)
    assert Bounds(10, 20, 100, 60) - Insets(20, 10, 50, 5) == Bounds(15, 40, 85, 0)


def test_bounds_location():
    assert Bounds(10, 20, 100, 200).location == Point(10, 20)


def test_bounds_size():
    assert Bounds(10, 20, 100, 200).size == Dimension(100, 200)


def test_bounds_points():
    points = (Point(-10, 20), Point(70, 20), Point(70, 60), Point(-10, 60))

    assert Bounds(-10, 20, 80, 40).points == points


def test_bounds_contains():
    assert Bounds(10, 20, 100, 50).contains(Point(60, 40))
    assert not Bounds(10, 20, 100, 50).contains(Point(0, 40))
    assert Bounds(-50, -40, 100, 80).contains(Point(50, 0))
    assert not Bounds(-50, -40, 100, 80).contains(Point(51, 0))


def test_insets_init():
    assert Insets(5, 10, 120, 0).top == 5
    assert Insets(15, 30, 0, 30.5).right == 30
    assert Insets(5, 10, 120, 0).bottom == 120
    assert Insets(15, 30, 0, 30.5).left == 30.5

    with raises(ValueError) as e_top:
        Insets(-10, 0, 10, 30)

    assert e_top.value.args[0] == "Argument 'top' must be zero or a positive number."

    with raises(ValueError) as e_right:
        Insets(20, -1, 10, 0)

    assert e_right.value.args[0] == "Argument 'right' must be zero or a positive number."

    with raises(ValueError) as e_bottom:
        Insets(5, 0, -15, 30)

    assert e_bottom.value.args[0] == "Argument 'bottom' must be zero or a positive number."

    with raises(ValueError) as e_left:
        Insets(0, 0, 40, -30)

    assert e_left.value.args[0] == "Argument 'left' must be zero or a positive number."


def test_insets_unpack():
    (top, right, bottom, left) = Insets(10, 30, 5, 20)

    assert top == 10
    assert right == 30
    assert bottom == 5
    assert left == 20


def test_insets_to_tuple():
    assert Insets(30, 20, 15, 5).tuple == (30, 20, 15, 5)


def test_insets_from_tuple():
    assert Insets.from_tuple((30, 0, 50, 40)) == Insets(30, 0, 50, 40)


def test_insets_copy():
    assert Insets(15, 10, 30, 30).copy(right=20, bottom=0) == Insets(15, 20, 0, 30)
    assert Insets(10, 10, 0, 10).copy(top=20, left=30) == Insets(20, 10, 0, 30)
    assert Insets(0, 0, 20, 40).copy(top=5, right=10, bottom=0, left=30) == Insets(5, 10, 0, 30)
    assert Insets(20, 10, 5, 30).copy() == Insets(20, 10, 5, 30)


def test_insets_operations():
    assert Insets(0, 0, 10, 20) + Insets(5, 10, 15, 10) == Insets(5, 10, 25, 30)
    assert Insets(15, 10, 0, 5) + 5 == Insets(20, 15, 5, 10)
    assert Insets(0, 5, 10, 20) - Insets(5, 10, 15, 10) == Insets(0, 0, 0, 10)
    assert Insets(15, 10, 20, 5) - 10 == Insets(5, 0, 10, 0)
    assert Insets(0, 10, 5, 30) * 2 == Insets(0, 20, 10, 60)
    assert Insets(20, 0, 10, 5) / 2 == Insets(10, 0, 5, 2.5)


def test_rgba_init():
    assert RGBA(0.5, 0.12, 0.2, 1).r == 0.5
    assert RGBA(0.5, 0.12, 0.2, 1).g == 0.12
    assert RGBA(0.5, 0.12, 0.2, 1).b == 0.2
    assert RGBA(0.5, 0.12, 0.2, 1).a == 1

    base = {"r": 0.5, "g": 0.5, "b": 0.5, "a": 0.5}

    for attr in ["r", "g", "b", "a"]:
        for value in [-0.1, 1.1]:
            args = base.copy()
            args[attr] = value

    with raises(ValueError) as e:
        RGBA(**args)

    assert e.value.args[0] == f"Argument '{attr}' must be between 0 and 1."


def test_rgba_unpack():
    (r, g, b, a) = RGBA(0.1, 0.2, 0.8, 1.0)

    assert r == 0.1
    assert g == 0.2
    assert b == 0.8
    assert a == 1.0


def test_rgba_to_tuple():
    assert RGBA(0.1, 0.2, 0.8, 1.0).tuple == (0.1, 0.2, 0.8, 1.0)


def test_rgba_from_tuple():
    assert RGBA.from_tuple((0.1, 0.2, 0.8, 1.0)) == RGBA(0.1, 0.2, 0.8, 1.0)


def test_rgba_copy():
    assert RGBA(0.1, 0.2, 0.8, 1.0).copy(r=0.4, a=0.3) == RGBA(0.4, 0.2, 0.8, 0.3)
    assert RGBA(0.1, 0.2, 0.8, 1.0).copy(g=0.5, b=0.1) == RGBA(0.1, 0.5, 0.1, 1.0)
    assert RGBA(0.1, 0.2, 0.8, 1.0).copy(r=0.3, g=0.1, b=0.4, a=0.4) == RGBA(0.3, 0.1, 0.4, 0.4)
    assert RGBA(0.1, 0.2, 0.8, 1.0).copy() == RGBA(0.1, 0.2, 0.8, 1.0)
