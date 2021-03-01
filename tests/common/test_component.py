from returns.result import Success

from alleycat.common import BaseComponent


def test_read_arg():
    config = BaseComponent.read_arg({"a": 1, "b": "B"})

    assert config("a", int) == Success(1)
    assert config("b", str) == Success("B")

    assert str(config("c", str).swap().unwrap()) == "Missing component property 'c'."
    assert str(config("a", str).swap().unwrap()) == "Component property 'a' has an invalid value: '1'."
