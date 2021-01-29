from __future__ import annotations

from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture

from alleycat.input import Input, InputBinding, InputMap


class TestBinding(InputBinding[float]):

    # noinspection PyMethodMayBeStatic
    def from_config(self, conf: dict):
        return TestBinding(conf["name"])


@fixture
def input_factory():
    return FactoryAggregate()


@fixture
def binding_factory():
    return FactoryAggregate(test=Factory(TestBinding.from_config), )


def test_from_config(binding_factory: providers.Provider[InputBinding], input_factory: providers.Provider[Input]):
    config = {
        "general": {
            "menu": {
                "type": "test",
                "name": "Exit Game"
            }
        },
        "view": {
            "rotate": {
                "type": "test",
                "name": "Rotate Camera"
            },
            "move": {
                "type": "test",
                "name": "Move Camera"
            }
        }
    }

    mapping = InputMap.from_config(binding_factory, input_factory, config)

    assert mapping
    assert len(mapping) == 2
    assert set(mapping.keys()) == {"general", "view"}

    assert mapping["general"]["menu"].name == "Exit Game"
    assert mapping["view"]["rotate"].name == "Rotate Camera"
    assert mapping["view"]["move"].name == "Move Camera"
