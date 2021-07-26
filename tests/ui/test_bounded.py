from pytest import fixture
from alleycat.reactive import functions as rv

from alleycat.ui import Bounded, Bounds, Dimension, Point


class Fixture(Bounded):
    pass


@fixture
def fixture() -> Fixture:
    return Fixture()


def test_bounds(fixture: Bounded):
    bounds = []

    rv.observe(fixture.bounds).subscribe(bounds.append)

    assert fixture.bounds == Bounds(0, 0, 0, 0)
    assert bounds == [Bounds(0, 0, 0, 0)]

    fixture.bounds = Bounds(-10, 30, 100, 200)

    assert fixture.bounds == Bounds(-10, 30, 100, 200)
    assert bounds == [Bounds(0, 0, 0, 0), Bounds(-10, 30, 100, 200)]


def test_location(fixture: Bounded):
    locations = []

    rv.observe(fixture.location).subscribe(locations.append)

    assert fixture.location == Point(0, 0)
    assert locations == [Point(0, 0)]

    fixture.bounds = Bounds(10, -30, 200, 100)

    assert fixture.location == Point(10, -30)
    assert locations == [Point(0, 0), Point(10, -30)]


def test_size(fixture: Bounded):
    sizes = []

    rv.observe(fixture.size).subscribe(sizes.append)

    assert fixture.size == Dimension(0, 0)
    assert sizes == [Dimension(0, 0)]

    fixture.bounds = Bounds(0, 0, 50, 150)

    assert fixture.size == Dimension(50, 150)
    assert sizes == [Dimension(0, 0), Dimension(50, 150)]
