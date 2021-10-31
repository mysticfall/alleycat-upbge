from types import ModuleType

from tests.mock import mock_module


def setup() -> None:
    mock_module("bpy.path", setup_path)
    mock_module("bpy.types", setup_types)


# noinspection PyPep8Naming
def setup_path(module: ModuleType) -> None:
    def abspath(path: str) -> str:
        return path

    module.abspath = abspath


# noinspection PyPep8Naming
def setup_types(module: ModuleType) -> None:
    class ID:
        pass

    class Object:
        pass

    module.ID = ID
    module.Object = Object
