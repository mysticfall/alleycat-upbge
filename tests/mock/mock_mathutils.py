from types import ModuleType

from tests.mock import mock_module


def setup() -> None:
    mock_module("mathutils", setup_module)


# noinspection PyPep8Naming
def setup_module(module: ModuleType) -> None:
    class Vector:
        pass

    module.Vector = Vector
