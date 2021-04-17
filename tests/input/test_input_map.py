from __future__ import annotations

from typing import Mapping

from alleycat.reactive import RP, RV, functions as rv
from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture, raises
from returns.functions import raise_exception
from returns.maybe import Nothing, Some
from returns.result import Success
from rx import Observable

from alleycat.input import Input, InputBinding, InputMap


class TestBinding(InputBinding[float]):
    current: RP[float] = rv.from_value(0.0)

    value: RV[float] = current.as_view()

    def __init__(self, name: str):
        super().__init__(name)

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
                "name": "Show Menu"
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
        },
        "quit": {
            "type": "test",
            "name": "Exit Game"
        }
    }


def test_from_config(
        config: Mapping,
        binding_factory: providers.Provider[InputBinding],
        input_factory: providers.Provider[Input]):
    mapping = InputMap.from_config(binding_factory, input_factory, config)

    assert mapping
    assert len(mapping) == 3
    assert set(mapping.keys()) == {"general", "view", "quit"}

    assert mapping["general"]["menu"].name == "Show Menu"
    assert mapping["general"]["debug"]["console"].name == "Open Game Console"
    assert mapping["view"]["rotate"].name == "Rotate Camera"
    assert mapping["view"]["move"].name == "Move Camera"
    assert mapping["quit"].name == "Exit Game"


def test_find_binding(
        config: Mapping,
        binding_factory: providers.Provider[InputBinding],
        input_factory: providers.Provider[Input]):
    mapping = InputMap.from_config(binding_factory, input_factory, config)

    assert mapping.find_binding("quit").map(lambda b: b.name) == Some("Exit Game")
    assert mapping.find_binding("general/menu").map(lambda b: b.name) == Some("Show Menu")
    assert mapping.find_binding("view/zoom").map(lambda b: b.name) == Nothing


def test_require_binding(
        config: Mapping,
        binding_factory: providers.Provider[InputBinding],
        input_factory: providers.Provider[Input]):
    mapping = InputMap.from_config(binding_factory, input_factory, config)

    assert mapping.require_binding("quit").map(lambda b: b.name) == Success("Exit Game")
    assert mapping.require_binding("general/menu").map(lambda b: b.name) == Success("Show Menu")

    with raises(ValueError) as e:
        mapping.require_binding("view/zoom").map(lambda b: b.name).alt(raise_exception)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "Unknown input path: 'view/zoom'."


def test_observe(
        config: Mapping,
        binding_factory: providers.Provider[InputBinding],
        input_factory: providers.Provider[Input]):
    mapping = InputMap.from_config(binding_factory, input_factory, config)

    binding: TestBinding = mapping["view"]["rotate"]

    assert binding

    value = mapping.observe("view/rotate").unwrap()

    assert isinstance(value, Observable)

    values = []
    value.subscribe(values.append)

    assert values == [0.0]

    binding.current = 0.5

    assert values == [0.0, 0.5]

    error = mapping.observe("view/zoom").swap().unwrap()

    assert isinstance(error, ValueError)
    assert str(error) == "Unknown input path: 'view/zoom'."
