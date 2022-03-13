from types import ModuleType

from alleycat.test import mock_module


def setup() -> None:
    def setup_bpy(module: ModuleType):
        module.path = mock_module("bpy.path", setup_path)
        module.types = mock_module("bpy.types", setup_types)

    mock_module("bpy", setup_bpy)


def setup_path(module: ModuleType) -> None:
    def abspath(path: str) -> str:
        return path

    module.abspath = abspath


def setup_types(module: ModuleType) -> None:
    class ID:
        pass

    class Object:
        pass

    class Camera:
        pass

    class Light:
        pass

    module.ID = ID
    module.Object = Object
    module.Camera = Camera
    module.Light = Light
