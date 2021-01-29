from dependency_injector import providers
from dependency_injector.providers import Factory, FactoryAggregate
from pytest import fixture, raises
from returns.maybe import Nothing, Some
from validator_collection.errors import JSONValidationError

from alleycat.input import Input, KeyPressInput, MouseButtonInput, TriggerBinding


@fixture
def input_factory() -> providers.Provider[Input]:
    return FactoryAggregate(
        key_press=Factory(KeyPressInput.from_config),
        mouse_button=Factory(MouseButtonInput.from_config),
        mouse_axis=Factory(MouseButtonInput.from_config), )


@fixture
def config():
    return {
        "type": "trigger",
        "name": "Show Menu",
        "description": "Toggle the main menu."
    }


def test_from_config(input_factory, config):
    binding = TriggerBinding.from_config(input_factory, config)

    assert binding
    assert binding.name == "Show Menu"
    assert binding.description == Some("Toggle the main menu.")


def test_from_config_missing_type(input_factory, config):
    del config["type"]

    with raises(JSONValidationError) as e:
        TriggerBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'type' is a required property"


def test_from_config_wrong_type(input_factory, config):
    config["type"] = "axis"

    with raises(JSONValidationError) as e:
        TriggerBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'trigger' was expected"


def test_from_config_missing_name(input_factory, config):
    del config["name"]

    with raises(JSONValidationError) as e:
        TriggerBinding.from_config(input_factory, config)

    assert e and e.value and len(e.value.args) > 0
    assert e.value.args[0] == "'name' is a required property"


def test_from_config_missing_description(input_factory, config):
    del config["description"]

    binding = TriggerBinding.from_config(input_factory, config)

    assert binding
    assert binding.name == "Show Menu"
    assert binding.description == Nothing
