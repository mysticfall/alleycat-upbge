from __future__ import annotations

from alleycat.reactive import functions as rv
from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture, raises
from returns.maybe import Nothing, Some
from rx import Observable
from rx.subject import BehaviorSubject
from validator_collection.errors import JSONValidationError

from alleycat.event import EventLoopScheduler
from alleycat.input import AxisBinding, AxisInput, Input


class TestInput(AxisInput):

    def __init__(self) -> None:
        self.subject = BehaviorSubject(0.0)
        self._scheduler = EventLoopScheduler()

        super().__init__()

    def create(self) -> Observable:
        return self.subject

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self._scheduler


@fixture
def input_factory() -> providers.Provider[Input]:
    return FactoryAggregate(test=Factory(lambda c: TestInput()))


def test_from_config(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis",
        "name": "Axis Binding",
        "description": "Axis Binding Test",
        "input": {
            "type": "test"
        }
    }

    binding = AxisBinding.from_config(input_factory, config)

    assert binding
    assert isinstance(binding, AxisBinding)
    assert binding.name == "Axis Binding"
    assert binding.description.unwrap() == "Axis Binding Test"
    assert isinstance(binding.input.unwrap(), TestInput)


def test_from_default_config(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis",
        "name": "Axis Binding"
    }

    binding = AxisBinding.from_config(input_factory, config)

    assert binding
    assert isinstance(binding, AxisBinding)
    assert binding.name == "Axis Binding"
    assert binding.description == Nothing
    assert binding.input == Nothing


def test_from_config_missing_type(input_factory: providers.Provider[Input]):
    config = {
        "name": "Axis Binding"
    }

    with raises(JSONValidationError) as e:
        AxisBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis2d",
        "name": "Axis Binding"
    }

    with raises(JSONValidationError) as e:
        AxisBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'axis' was expected"


def test_value():
    # noinspection PyShadowingBuiltins
    input = TestInput()

    binding = AxisBinding("test", input=input)

    values = []

    rv.observe(binding.value).subscribe(values.append)

    assert binding.value == 0.0
    assert values == [0.0]

    input.subject.on_next(0.5)

    assert binding.value == 0.5
    assert len(values) == 2
    assert values[-1] == 0.5


def test_switch_input():
    input1 = TestInput()
    input2 = TestInput()

    binding = AxisBinding("test", input=input1)

    input1.subject.on_next(0.3)
    input2.subject.on_next(0.6)

    assert binding.value == 0.3

    binding.input = Some(input2)

    input1.subject.on_next(0.1)
    input2.subject.on_next(0.7)

    assert binding.value == 0.7


def test_lazy_bound_input():
    binding = AxisBinding("test")

    assert binding.value == 0.0

    # noinspection PyShadowingBuiltins
    input = TestInput()
    input.subject.on_next(0.4)

    binding.input = Some(input)

    assert binding.value == 0.4
