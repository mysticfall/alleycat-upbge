from pytest import fixture
from returns.maybe import Nothing, Some
from returns.result import Success

from alleycat.common import MapReader


@fixture
def args() -> dict:
    return {"a": 1, "b": "B"}


def test_read(args: dict):
    config = MapReader(args).read

    assert config("a", int) == Some(1)
    assert config("b", str) == Some("B")

    assert config("c", str) == Nothing
    assert config("a", str) == Nothing


def test_require(args: dict):
    config = MapReader(args).require

    assert config("a", int) == Success(1)
    assert config("b", str) == Success("B")

    assert str(config("c", str).swap().unwrap()) == "Missing required argument 'c'."
    assert str(config("a", str).swap().unwrap()) == "Argument 'a' has an invalid value: '1'."


def test_mapping(args: dict):
    configs = MapReader(args)

    assert len(configs) == 2

    assert configs["a"] == 1
    assert configs["b"] == "B"

    assert configs.keys() == {"a", "b"}
