from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from unittest.mock import patch

from alleycat.reactive import RP, functions as rv
from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture, raises
from returns.maybe import Nothing, Some
from rx import Observable
from validator_collection.errors import JSONValidationError

from alleycat.input import Axis2DBinding, AxisInput, Input


@dataclass(frozen=True)
class TestVector:
    values: Tuple[float, float]


class TestAxisInput(AxisInput):
    test_value: RP[float] = rv.from_value(0.0)

    def create(self) -> Observable:
        return self.observe("test_value")

    # noinspection PyUnusedLocal
    @classmethod
    def from_config(cls, conf: dict) -> TestAxisInput:
        return TestAxisInput()


@fixture
def input_factory() -> providers.Provider[Input]:
    return FactoryAggregate(test=Factory(TestAxisInput.from_config), )


def test_from_config(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis2d",
        "name": "Look Around",
        "description": "Rotate the current view.",
        "input": {
            "x": {
                "type": "test"
            },
            "y": {
                "type": "test"
            }
        }
    }

    binding = Axis2DBinding.from_config(input_factory, config)

    assert isinstance(binding, Axis2DBinding)
    assert binding.name == "Look Around"
    assert binding.description == Some("Rotate the current view.")

    assert isinstance(binding.x_input.unwrap(), TestAxisInput)
    assert isinstance(binding.y_input.unwrap(), TestAxisInput)


def test_from_default_config(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis2d",
        "name": "Look Around"
    }

    binding = Axis2DBinding.from_config(input_factory, config)

    assert isinstance(binding, Axis2DBinding)
    assert binding.name == "Look Around"
    assert binding.description == Nothing

    assert binding.x_input == Nothing
    assert binding.y_input == Nothing


def test_from_config_missing_type(input_factory: providers.Provider[Input]):
    config = {
        "name": "Look Around",
        "description": "Rotate the current view."
    }

    with raises(JSONValidationError) as e:
        Axis2DBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(input_factory: providers.Provider[Input]):
    config = {
        "type": "trigger",
        "name": "Look Around",
        "description": "Rotate the current view."
    }

    with raises(JSONValidationError) as e:
        Axis2DBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'axis2d' was expected"


@patch("mathutils.Vector", TestVector)
def test_value():
    x = TestAxisInput()
    y = TestAxisInput()

    binding = Axis2DBinding("test", x_input=x, y_input=y)

    values = []

    rv.observe(binding.value).subscribe(values.append)

    assert binding.value == TestVector((0.0, 0.0))
    assert values == [TestVector((0.0, 0.0))]

    x.test_value = 0.3

    assert binding.value == TestVector((0.3, 0.0))
    assert len(values) == 2
    assert values[-1] == TestVector((0.3, 0.0))

    y.test_value = 0.6

    assert binding.value == TestVector((0.3, 0.6))
    assert len(values) == 3
    assert values[-1] == TestVector((0.3, 0.6))


@patch("mathutils.Vector", TestVector)
def test_switch_input():
    x1 = TestAxisInput()
    y1 = TestAxisInput()

    x1.test_value = 0.1
    y1.test_value = 0.8

    binding = Axis2DBinding("test", x_input=x1, y_input=y1)

    assert binding.value == TestVector((0.1, 0.8))

    x2 = TestAxisInput()
    y2 = TestAxisInput()

    x2.test_value = 0.3
    y2.test_value = 0.4

    binding.x_input = Some(x2)
    binding.y_input = Some(y2)

    assert binding.value == TestVector((0.3, 0.4))


@patch("mathutils.Vector", TestVector)
def test_lazy_bound_input():
    binding = Axis2DBinding("test")

    assert binding.value == TestVector((0.0, 0.0))

    x = TestAxisInput()
    y = TestAxisInput()

    x.test_value = 0.7
    y.test_value = 0.6

    binding.x_input = Some(x)
    binding.y_input = Some(y)

    assert binding.value == TestVector((0.7, 0.6))
