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
from alleycat.input import TriggerBinding, TriggerInput, Input


class TestInput(TriggerInput):

    def __init__(self) -> None:
        self.subject = BehaviorSubject(False)
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
        "type": "trigger",
        "name": "Trigger Binding",
        "description": "Trigger Binding Test",
        "input": {
            "type": "test"
        }
    }

    binding = TriggerBinding.from_config(input_factory, config)

    assert binding
    assert isinstance(binding, TriggerBinding)
    assert binding.name == "Trigger Binding"
    assert binding.description.unwrap() == "Trigger Binding Test"
    assert isinstance(binding.input.unwrap(), TestInput)


def test_from_default_config(input_factory: providers.Provider[Input]):
    config = {
        "type": "trigger",
        "name": "Trigger Binding"
    }

    binding = TriggerBinding.from_config(input_factory, config)

    assert binding
    assert isinstance(binding, TriggerBinding)
    assert binding.name == "Trigger Binding"
    assert binding.description == Nothing
    assert binding.input == Nothing


def test_from_config_missing_type(input_factory: providers.Provider[Input]):
    config = {
        "name": "Trigger Binding"
    }

    with raises(JSONValidationError) as e:
        TriggerBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(input_factory: providers.Provider[Input]):
    config = {
        "type": "axis",
        "name": "Trigger Binding"
    }

    with raises(JSONValidationError) as e:
        TriggerBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'trigger' was expected"


def test_value():
    # noinspection PyShadowingBuiltins
    input = TestInput()

    binding = TriggerBinding("test", input=input)

    values = []

    rv.observe(binding.value).subscribe(values.append)

    assert not binding.value
    assert values == [False]

    input.subject.on_next(True)

    assert binding.value
    assert len(values) == 2
    assert values[-1]


def test_switch_input():
    input1 = TestInput()
    input2 = TestInput()

    binding = TriggerBinding("test", input=input1)

    input1.subject.on_next(True)
    input2.subject.on_next(False)

    assert binding.value

    binding.input = Some(input2)

    input1.subject.on_next(False)
    input2.subject.on_next(True)

    assert binding.value


def test_lazy_bound_input():
    binding = TriggerBinding("test")

    assert binding.value == 0.0

    # noinspection PyShadowingBuiltins
    input = TestInput()
    input.subject.on_next(0.4)

    binding.input = Some(input)

    assert binding.value == 0.4
