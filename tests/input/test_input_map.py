from __future__ import annotations

from typing import Mapping

from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture

from alleycat.input import Input, InputBinding, InputMap


class TestBinding(InputBinding[float]):

    # noinspection PyMethodMayBeStatic
    def from_config(self, conf: dict):
        return TestBinding(conf["name"])


@fixture
def input_factory() -> providers.Provider[Input]:
    return FactoryAggregate()


@fixture
def binding_factory() -> providers.Provider[InputBinding]:
    return FactoryAggregate(test=Factory(TestBinding.from_config), )


@fixture
def config() -> Mapping:
    return {
        "general": {
            "menu": {
                "type": "test",
                "name": "Exit Game"
            },
            "debug": {
                "console": {
                    "type": "test",
                    "name": "Open Game Console"
                }
            },
            "invalid": "Invalid entry"
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


def test_from_config(
        config: Mapping,
        binding_factory: providers.Provider[InputBinding],
        input_factory: providers.Provider[Input]):
    mapping = InputMap.from_config(binding_factory, input_factory, config)

    assert mapping
    assert len(mapping) == 2
    assert set(mapping.keys()) == {"general", "view"}

    assert mapping["general"]["menu"].name == "Exit Game"
    assert mapping["general"]["debug"]["console"].name == "Open Game Console"
    assert mapping["view"]["rotate"].name == "Rotate Camera"
    assert mapping["view"]["move"].name == "Move Camera"
