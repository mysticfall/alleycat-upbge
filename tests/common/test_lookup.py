from pytest import fixture, raises
from returns.maybe import Nothing, Some

from alleycat.common import Lookup


@fixture(scope="module")
def lookup() -> Lookup[int]:
    class LookupFixture(Lookup[int]):
        pass

    return LookupFixture({"a": 1, "b": 2, "c": 5})


def test_len(lookup: Lookup[int]):
    assert len(lookup) == 3


def test_get_item(lookup: Lookup[int]):
    assert lookup["a"] == 1
    assert lookup["b"] == 2
    assert lookup["c"] == 5

    with raises(KeyError) as err:
        # noinspection PyStatementEffect
        lookup["d"]

    assert str(err.value) == "'d'"


def test_contains(lookup: Lookup[int]):
    assert "a" in lookup
    assert "b" in lookup
    assert "c" in lookup
    assert "d" not in lookup


def test_iter(lookup: Lookup[int]):
    it = iter(lookup)

    assert next(it) == "a"
    assert next(it) == "b"
    assert next(it) == "c"

    with raises(StopIteration):
        next(it)


def test_find(lookup: Lookup[int]):
    assert lookup.find("a") == Some(1)
    assert lookup.find("b") == Some(2)
    assert lookup.find("c") == Some(5)
    assert lookup.find("d") == Nothing
