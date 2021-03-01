from _pytest.fixtures import fixture
from returns.maybe import Nothing, Some
from returns.result import Success

from alleycat.common import ArgumentReader


@fixture
def args() -> dict:
    return {"a": 1, "b": "B"}


def test_read(args: dict):
    config = ArgumentReader(args).read

    assert config("a", int) == Some(1)
    assert config("b", str) == Some("B")

    assert config("c", str) == Nothing
    assert config("a", str) == Nothing


def test_require(args: dict):
    config = ArgumentReader(args).require

    assert config("a", int) == Success(1)
    assert config("b", str) == Success("B")

    assert str(config("c", str).swap().unwrap()) == "Missing component property 'c'."
    assert str(config("a", str).swap().unwrap()) == "Component property 'a' has an invalid value: '1'."
