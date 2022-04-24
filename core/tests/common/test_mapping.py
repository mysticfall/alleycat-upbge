from pytest import fixture
from returns.maybe import Nothing, Some
from returns.result import Success

from alleycat.common import MapReader


@fixture
def args() -> dict:
    return {"a": 1, "b": "B", "c": None}


def test_read(args: dict):
    config = MapReader(args).read

    assert config("a", int) == Some(1)
    assert config("b", str) == Some("B")
    assert config("c", str) == Nothing

    assert config("c", str) == Nothing
    assert config("a", str) == Nothing
    assert config("c", int) == Nothing


def test_require(args: dict):
    config = MapReader(args).require

    assert config("a", int) == Success(1)
    assert config("b", str) == Success("B")

    assert str(config("a", str).swap().unwrap()) == "Argument 'a' has an invalid value: '1'."
    assert str(config("c", str).swap().unwrap()) == "Missing required argument 'c'."
    assert str(config("d", str).swap().unwrap()) == "Missing required argument 'd'."


def test_mapping(args: dict):
    configs = MapReader(args)

    assert len(configs) == 3

    assert configs["a"] == 1
    assert configs["b"] == "B"
    assert configs["c"] is None

    assert configs.keys() == {"a", "b", "c"}
